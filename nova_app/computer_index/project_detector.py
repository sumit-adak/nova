"""Developer project and repository detection scanner."""
import os
from datetime import datetime, timezone
from pathlib import Path
import structlog
from sqlalchemy import select
from nova_app.config.settings import Settings, get_settings
from nova_app.db.models.computer_index import DetectedProject
from nova_app.db.session import get_session_factory

logger = structlog.get_logger(__name__)

PROJECT_MARKERS = {
    ".git": ("git", "generic"),
    "pyproject.toml": ("git", "python"),
    "requirements.txt": ("git", "python"),
    "setup.py": ("git", "python"),
    "package.json": ("git", "node"),
    "Cargo.toml": ("git", "rust"),
    "go.mod": ("git", "go"),
    "pom.xml": ("git", "java"),
    "build.gradle": ("git", "java/kotlin"),
    "CMakeLists.txt": ("git", "cpp"),
}


class ProjectDetector:
    """Detects software projects in allow-listed directories and syncs to SQLite."""

    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()

    def detect_project_type(self, folder: Path) -> tuple[str, str] | None:
        """Determine VCS and project language type from files in directory."""
        vcs = "none"
        project_type = "generic"

        if (folder / ".git").exists():
            vcs = "git"

        for marker, (marker_vcs, ptype) in PROJECT_MARKERS.items():
            if marker != ".git" and (folder / marker).exists():
                project_type = ptype
                if vcs == "none":
                    vcs = marker_vcs
                return vcs, project_type

        if vcs != "none":
            return vcs, project_type

        return None

    async def scan_directories(self, roots: list[str | Path] | None = None) -> list[dict]:
        """Scan directories up to 3 levels deep for project roots."""
        scan_roots = roots or self.settings.allowed_roots
        detected = []

        session_factory = get_session_factory()
        async with session_factory() as session:
            for root_str in scan_roots:
                root_path = Path(root_str).resolve()
                if not root_path.is_dir():
                    continue

                for current_root, dirs, _ in os.walk(root_path):
                    # Limit depth to 3 levels from root
                    rel = Path(current_root).relative_to(root_path)
                    if len(rel.parts) > 3:
                        dirs[:] = []
                        continue

                    # Prune dependency folders
                    dirs[:] = [
                        d for d in dirs
                        if not d.startswith(".")
                        and d not in ["node_modules", ".venv", "venv", "__pycache__", "build", "dist"]
                    ]

                    curr_folder = Path(current_root)
                    type_info = self.detect_project_type(curr_folder)

                    if type_info:
                        vcs, ptype = type_info
                        proj_name = curr_folder.name
                        path_str = str(curr_folder)

                        # Upsert to DB
                        stmt = select(DetectedProject).where(DetectedProject.root_path == path_str)
                        res = await session.execute(stmt)
                        existing = res.scalar_one_or_none()

                        if existing:
                            existing.name = proj_name
                            existing.project_type = ptype
                            existing.vcs = vcs
                            existing.detected_at = datetime.now(timezone.utc)
                        else:
                            new_proj = DetectedProject(
                                root_path=path_str,
                                name=proj_name,
                                project_type=pttype if "pttype" in locals() else ptype,
                                vcs=vcs,
                                detected_at=datetime.now(timezone.utc),
                            )
                            session.add(new_proj)

                        detected.append({
                            "name": proj_name,
                            "path": path_str,
                            "type": ptype,
                            "vcs": vcs,
                        })

                        # Do not recurse further inside a detected project folder
                        dirs[:] = []

            await session.commit()

        logger.info("Project scanning completed", total_detected=len(detected))
        return detected


_project_detector_instance: ProjectDetector | None = None


def get_project_detector() -> ProjectDetector:
    """Get singleton ProjectDetector instance."""
    global _project_detector_instance
    if _project_detector_instance is None:
        _project_detector_instance = ProjectDetector()
    return _project_detector_instance
