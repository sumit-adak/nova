"""GPU monitoring with graceful fallback."""

from __future__ import annotations

from app.core.logger import get_logger

logger = get_logger("gpu")


class GPUMonitor:
    """Monitor GPU usage when hardware support is available."""

    def __init__(self) -> None:
        self._gputil_available = False
        try:
            import GPUtil  # noqa: F401
            self._gputil_available = True
        except ImportError:
            logger.info("GPUtil not available - GPU metrics disabled")

    def get_usage(self) -> dict:
        """Return GPU usage metrics or unavailable status."""
        if not self._gputil_available:
            return self._fallback()

        try:
            import GPUtil
            gpus = GPUtil.getGPUs()
            if not gpus:
                return self._fallback()

            gpu = gpus[0]
            return {
                "available": True,
                "name": gpu.name,
                "load": round(gpu.load * 100, 1),
                "memory_used": round(gpu.memoryUsed),
                "memory_total": round(gpu.memoryTotal),
                "temperature": gpu.temperature,
            }
        except Exception as exc:
            logger.debug("GPU query failed: %s", exc)
            return self._fallback()

    @staticmethod
    def _fallback() -> dict:
        return {
            "available": False,
            "name": "N/A",
            "load": 0,
            "memory_used": 0,
            "memory_total": 0,
            "temperature": None,
        }
