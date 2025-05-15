import asyncio
import contextlib
import typing

from loguru import logger


class BroadcastManager[T]:
    """Broadcast manager that broadcasts an item to its open queues

    The manager supports opening read queues that receive items broadcast by :py:meth:`broadcast` or :py:meth:`broadcast_nowait`. A read queue can
    be obtained by :
        * calling :py:meth:`output` which returns an asynchronous context manager yielding a queue on enter (queue is closed on exit),
        * calling :py:meth:`open_queue` (note that :py:meth:`close_queue` must be called to close the queue).
    """

    _queues: set[asyncio.Queue[T]]

    def __init__(self):
        self._queues = set()

    def __contains__(self, item):
        return item in self._queues

    def _subscribe(self):
        logger.debug("Subscribing")
        queue = asyncio.Queue()
        self._queues.add(queue)

        return queue

    def _unsubscribe(self, queue: asyncio.Queue[T]):
        logger.debug("Unsubscribing")
        self._queues.remove(queue)

    @contextlib.contextmanager
    def output(self) -> typing.Iterator[asyncio.Queue[T]]:
        """Returns an asynchronous context manager that opens a new queue on enter and closes it on exit"""
        logger.debug("Opening output")
        queue = self._subscribe()
        try:
            yield queue
        finally:
            logger.debug("Closing output")
            self._unsubscribe(queue)

    async def broadcast(self, item: T):
        """Broadcasts the item to all open queues. Blocking variant."""
        logger.debug("Broadcasting", item=item)

        for queue in self._queues:
            await queue.put(item)

    def broadcast_nowait(self, item: T):
        """Broadcasts the item to all open queues. Non-blocking variant."""
        logger.debug("Broadcasting", item=item)

        for queue in self._queues:
            queue.put_nowait(item)
