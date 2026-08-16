"""Windows Application Registry scanner via Windows Registry and Start Menu."""
import os
import winreg
from pathlib import Path
from datetime import datetime, timezone
import structlog
from sqlalchemy import select
from nova_app.computer_index.models import DiscoveredApp
from nova_app.db.models.computer_index import InstalledApp
from nova_app.db.session import get_session_factory

logger = structlog.get_logger(__name__)


class WindowsAppRegistry:
    """Scans and synchronizes installed Windows applications into the database."""

    def scan_start_menu_shortcuts(self) -> list[DiscoveredApp]:
        """Scan common and user Start Menu folders for shortcuts."""
        shortcuts: list[DiscoveredApp] = []
        start_paths = [
            Path(os.environ.get("ProgramData", "C:\\ProgramData")) / "Microsoft\\Windows\\Start Menu\\Programs",
            Path(os.environ.get("APPDATA", "")) / "Microsoft\\Windows\\Start Menu\\Programs",
        ]

        for base in start_paths:
            if not base.exists():
                continue
            for root, _, files in os.walk(base):
                for f in files:
                    if f.lower().endswith(".lnk"):
                        app_name = Path(f).stem
                        full_shortcut = Path(root) / f
                        shortcuts.append(
                            DiscoveredApp(
                                name=app_name,
                                exec_path=str(full_shortcut),
                                publisher="Start Menu",
                            )
                        )
        return shortcuts

    def scan_windows_registry(self) -> list[DiscoveredApp]:
        """Scan HKLM and HKCU uninstall keys for installed applications."""
        apps: list[DiscoveredApp] = []
        reg_paths = [
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
            (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
        ]

        for root_key, sub_key in reg_paths:
            try:
                with winreg.OpenKey(root_key, sub_key) as key:
                    num_subkeys = winreg.QueryInfoKey(key)[0]
                    for i in range(num_subkeys):
                        try:
                            subkey_name = winreg.EnumKey(key, i)
                            with winreg.OpenKey(key, subkey_name) as app_key:
                                try:
                                    display_name = winreg.QueryValueEx(app_key, "DisplayName")[0]
                                    if not display_name or not display_name.strip():
                                        continue

                                    # Try to get install location or display icon
                                    exec_path = ""
                                    try:
                                        exec_path = winreg.QueryValueEx(app_key, "DisplayIcon")[0]
                                    except OSError:
                                        try:
                                            exec_path = winreg.QueryValueEx(app_key, "InstallLocation")[0]
                                        except OSError:
                                            exec_path = ""

                                    version = ""
                                    try:
                                        version = winreg.QueryValueEx(app_key, "DisplayVersion")[0]
                                    except OSError:
                                        version = None

                                    publisher = ""
                                    try:
                                        publisher = winreg.QueryValueEx(app_key, "Publisher")[0]
                                    except OSError:
                                        publisher = None

                                    apps.append(
                                        DiscoveredApp(
                                            name=display_name.strip(),
                                            exec_path=exec_path.strip(),
                                            version=str(version) if version else None,
                                            publisher=str(publisher) if publisher else None,
                                        )
                                    )
                                except OSError:
                                    continue
                        except OSError:
                            continue
            except OSError:
                continue

        return apps

    async def sync_applications_to_db(self) -> int:
        """Scan applications and store/update them in the SQLite DB."""
        found_apps = self.scan_start_menu_shortcuts() + self.scan_windows_registry()
        
        # Deduplicate by app name
        unique_apps: dict[str, DiscoveredApp] = {}
        for app in found_apps:
            if app.name not in unique_apps:
                unique_apps[app.name] = app

        session_factory = get_session_factory()
        count = 0
        async with session_factory() as session:
            for app in unique_apps.values():
                # Check if exists
                stmt = select(InstalledApp).where(InstalledApp.name == app.name)
                result = await session.execute(stmt)
                existing = result.scalar_one_or_none()

                if existing:
                    existing.exec_path = app.exec_path
                    existing.version = app.version
                    existing.publisher = app.publisher
                    existing.detected_at = datetime.now(timezone.utc)
                else:
                    new_app = InstalledApp(
                        name=app.name,
                        exec_path=app.exec_path,
                        version=app.version,
                        publisher=app.publisher,
                        detected_at=datetime.now(timezone.utc),
                    )
                    session.add(new_app)
                count += 1

            await session.commit()

        logger.info("Synchronized installed apps to database", total_apps=count)
        return count
