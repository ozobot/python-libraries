import asyncio
import logging
import typing
from asyncio import Task

from ozobot.ora.utils import log_errors

_TUnbound = typing.TypeVar("_TUnbound")

_logger = logging.getLogger(__name__)


class LazyTaskGroup:
    _pending_tasks: set[Task]
    _exceptions: list[BaseException]
    _waiter: asyncio.Future[None] | None

    @property
    def count(self) -> int:
        return len(self._pending_tasks)

    def __init__(self):
        self._pending_tasks = set()
        self._exceptions = list()
        self._waiter = None

    def create_task(
        self, coro: typing.Coroutine[_TUnbound, typing.Any, typing.Any], *, name: str | None = None
    ) -> asyncio.Task[_TUnbound]:
        task: Task[_TUnbound] = asyncio.create_task(coro, name=name)
        _logger.debug("Spawned task: id=%s, name=%s", id(task), name)
        task.add_done_callback(self._on_task_done)
        self._pending_tasks.add(task)

        return task

    @log_errors
    def _on_task_done(self, task: Task):
        _logger.debug("_on_task_done: task_id=%s, task_name: %s", id(task), task.get_name())
        self._pending_tasks.discard(task)
        exception = None

        try:
            ex = task.exception()
            exception = ex
        except asyncio.CancelledError:
            _logger.debug("Task cancelled")
        except Exception as ex:
            exception = ex

        if exception:
            _logger.debug("Task done with exception %s (id=%s)", exception, id(task))
            self._exceptions.append(exception)
            self._abort()
        else:
            _logger.debug("Task done successfully")

        if self._waiter:
            _logger.debug("Notifying task changes")
            self._waiter.set_result(None)
            self._waiter = None
        else:
            _logger.debug("No waiter")

    def validate_state(self) -> None:
        if self._exceptions:
            _logger.debug("Task group has exceptions %s", self._exceptions)

            self._abort()
            exceptions = self._exceptions
            self._exceptions = list()
            raise BaseExceptionGroup("unhandled errors in a LazyTaskGroup", exceptions)
        else:
            _logger.debug("Task group state is ok")

    def _abort(self) -> None:
        for task in self._pending_tasks:
            task.cancel()

    async def wait_for_change(self):
        _logger.debug("Waiting for task changes")

        if not self._waiter:
            self._waiter = asyncio.Future()

        waiter = self._waiter
        await waiter


class TaskQueue:
    _maxsize: int
    _tasks: LazyTaskGroup

    def __init__(self, maxsize: int):
        self._tasks = LazyTaskGroup()
        self._maxsize = maxsize

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self._tasks.validate_state()

    async def run_nonblocking(self, awaitable: typing.Awaitable[_TUnbound]) -> Task[_TUnbound]:
        _logger.debug("Running non-blocking awaitable: %s", awaitable)

        async def _task():
            await awaitable

        self._tasks.validate_state()
        await self._wait_for_queue()
        task = self._tasks.create_task(_task())

        return task

    async def run_blocking(self, awaitable: typing.Awaitable[typing.Any]) -> None:
        _logger.debug("Running blocking awaitable: %s", awaitable)
        t = await self.run_nonblocking(awaitable)

        try:
            await t
        except asyncio.CancelledError:
            self._tasks.validate_state()

    async def _wait_for_queue(self):
        while self._tasks.count >= self._maxsize:
            await self._tasks.wait_for_change()
            self._tasks.validate_state()
