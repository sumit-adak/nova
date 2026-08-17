"""Asyncio bridge running a dedicated background event loop for PySide6 integration."""
import asyncio
import threading
from typing import Any, Callable, Coroutine
import structlog
from PySide6.QtCore import QObject, Signal

logger = structlog.get_logger(__name__)


class BridgeSignals(QObject):
    """Qt Signals to cross the thread boundary safely into the Qt GUI thread."""
    task_done = Signal(object, object)  # (result, callback)
    task_error = Signal(object, object)  # (exception, err_callback)


class AsyncBridge:
    """Manages a background asyncio event loop and dispatches tasks thread-safely."""

    def __init__(self):
        self._loop: asyncio.AbstractEventLoop | None = None
        self._thread: threading.Thread | None = None
        self._is_running = False
        self._signals = BridgeSignals()
        self._signals.task_done.connect(self._on_task_done)
        self._signals.task_error.connect(self._on_task_error)

    def start(self) -> None:
        """Start the background event loop thread."""
        if self._is_running:
            return

        self._is_running = True
        self._loop_ready = threading.Event()
        self._thread = threading.Thread(target=self._run_loop, name="nova_async_bridge", daemon=True)
        self._thread.start()
        self._loop_ready.wait()
        logger.info("AsyncBridge background event loop started")

    def _run_loop(self) -> None:
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._loop_ready.set()
        try:
            self._loop.run_forever()
        finally:
            self._loop.close()

    def get_loop(self) -> asyncio.AbstractEventLoop:
        if self._loop is None:
            self.start()
        return self._loop  # type: ignore

    def run_coroutine(
        self,
        coro: Coroutine[Any, Any, Any],
        on_success: Callable[[Any], None] | None = None,
        on_error: Callable[[Exception], None] | None = None,
    ) -> asyncio.Future:
        """Schedule a coroutine on the background asyncio loop and notify callbacks on the Qt thread."""
        loop = self.get_loop()

        def _wrapper():
            async def _inner():
                try:
                    res = await coro
                    if on_success:
                        self._signals.task_done.emit(res, on_success)
                    return res
                except Exception as e:
                    logger.error("Error in async bridge coroutine", error=str(e))
                    if on_error:
                        self._signals.task_error.emit(e, on_error)
                    raise
            return asyncio.create_task(_inner())

        future = asyncio.run_coroutine_threadsafe(coro, loop)
        if on_success or on_error:
            def _future_done_cb(fut: asyncio.Future):
                try:
                    result = fut.result()
                    if on_success:
                        self._signals.task_done.emit(result, on_success)
                except Exception as e:
                    if on_error:
                        self._signals.task_error.emit(e, on_error)
            future.add_done_callback(_future_done_cb)

        return future

    def _on_task_done(self, result: Any, callback: Callable[[Any], None]) -> None:
        """Invoked on Qt main GUI thread."""
        try:
            callback(result)
        except Exception as e:
            logger.error("Error in on_task_done callback", error=str(e))

    def _on_task_error(self, exc: Exception, err_callback: Callable[[Exception], None]) -> None:
        """Invoked on Qt main GUI thread."""
        try:
            err_callback(exc)
        except Exception as e:
            logger.error("Error in on_task_error callback", error=str(e))

    def stop(self) -> None:
        """Stop background event loop."""
        if self._loop and self._loop.is_running():
            self._loop.call_soon_threadsafe(self._loop.stop)
        self._is_running = False


_bridge_instance: AsyncBridge | None = None


def get_async_bridge() -> AsyncBridge:
    """Get singleton AsyncBridge instance."""
    global _bridge_instance
    if _bridge_instance is None:
        _bridge_instance = AsyncBridge()
        _bridge_instance.start()
    return _bridge_instance
