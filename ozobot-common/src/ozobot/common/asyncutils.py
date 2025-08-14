import asyncio
import typing
from builtins import RuntimeError


async def async_iterator_never() -> typing.AsyncGenerator[typing.Never]:
    yield await asyncio.Future()


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
