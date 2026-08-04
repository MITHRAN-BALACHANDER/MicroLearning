"""
AsyncWorker - a dedicated asyncio loop running on a background thread.

The WhatsApp webhook is a synchronous Flask app but the agents are async, and
Meta retries any webhook that does not get a 200 within seconds. The webhook
therefore hands work to this worker and returns 200 immediately.

Keeping this loop separate from python-telegram-bot's loop means the two
channels cannot block each other when both are enabled.
"""
import asyncio
import threading
from concurrent.futures import Future
from typing import Any, Coroutine, Optional

from loguru import logger


class AsyncWorker:
    """Runs coroutines on a private event loop owned by a daemon thread."""

    def __init__(self, name: str = "async-worker"):
        self.name = name
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._thread: Optional[threading.Thread] = None
        self._ready = threading.Event()

    def start(self) -> "AsyncWorker":
        if self._thread is not None:
            return self

        def _run() -> None:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            self._loop = loop
            self._ready.set()
            try:
                loop.run_forever()
            finally:
                try:
                    loop.run_until_complete(loop.shutdown_asyncgens())
                finally:
                    loop.close()

        self._thread = threading.Thread(target=_run, name=self.name, daemon=True)
        self._thread.start()
        self._ready.wait(timeout=10)
        logger.info(f"AsyncWorker '{self.name}' started")
        return self

    @property
    def loop(self) -> asyncio.AbstractEventLoop:
        if self._loop is None:
            raise RuntimeError("AsyncWorker has not been started")
        return self._loop

    def submit(self, coro: Coroutine) -> Future:
        """Schedule a coroutine and return immediately."""
        future = asyncio.run_coroutine_threadsafe(coro, self.loop)
        future.add_done_callback(self._log_failure)
        return future

    def run(self, coro: Coroutine, timeout: Optional[float] = None) -> Any:
        """Schedule a coroutine and block until it finishes."""
        return asyncio.run_coroutine_threadsafe(coro, self.loop).result(timeout)

    @staticmethod
    def _log_failure(future: Future) -> None:
        if future.cancelled():
            return
        error = future.exception()
        if error is not None:
            logger.opt(exception=error).error(f"Background task failed: {error}")

    def stop(self, timeout: float = 5.0) -> None:
        if self._loop is None:
            return
        self._loop.call_soon_threadsafe(self._loop.stop)
        if self._thread is not None:
            self._thread.join(timeout=timeout)
        self._loop = None
        self._thread = None
        logger.info(f"AsyncWorker '{self.name}' stopped")
