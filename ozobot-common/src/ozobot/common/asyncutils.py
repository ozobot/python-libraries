import asyncio
import contextlib
import typing
from builtins import RuntimeError


async def async_iterator_never() -> typing.AsyncGenerator[typing.Never]:
    yield await asyncio.Future()


class BackgroundTask:
    """
    Runs a background task as an async context manager.

    Unlike asyncio.TaskGroup, exceptions from the background task are propagated
    directly instead of being wrapped in an ExceptionGroup.
    """

    def __init__(self) -> None:
        self._task: asyncio.Task | None = None
        self._exception: BaseException | None = None
        self._base_task: asyncio.Task | None = asyncio.current_task()

    async def __aenter__(self) -> typing.Self:
        return self

    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        if self._task:
            self._task.remove_done_callback(self._on_task_done)
            if not self._task.done():
                self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task

        if self._exception:
            raise self._exception

    def _on_task_done(self, task: asyncio.Task) -> None:
        if task.cancelled():
            return

        exception = task.exception()
        if exception is None:
            return

        self._exception = exception

        if self._base_task and not self._base_task.done():
            self._base_task.cancel()

    def start(self, coro: typing.Coroutine[typing.Any, typing.Any, typing.Any]) -> None:
        """Start the background task."""
        self._task = asyncio.create_task(coro)
        self._task.add_done_callback(self._on_task_done)


class CancellableTaskGroup(asyncio.TaskGroup):
    class _TaskGroupCancelledError(Exception): ...

    def __init__(self) -> None:
        super().__init__()
        self._suppress_cancellation_error = False

    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        try:
            return await super().__aexit__(exc_type, exc_value, traceback)
        except* self._TaskGroupCancelledError:
            if not self._suppress_cancellation_error:
                raise asyncio.CancelledError() from None

    def cancel_quietly(self) -> None:
        self._suppress_cancellation_error = True
        self.cancel()

    def cancel(self) -> None:
        async def _canceller() -> None:
            raise self._TaskGroupCancelledError()

        try:
            self.create_task(_canceller())
        except RuntimeError:
            pass  # tg is already shutting down, we can ignore this
