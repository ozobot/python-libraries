from __future__ import annotations

import contextlib
import socket
import typing
from asyncio import Queue, QueueShutDown
from collections.abc import AsyncIterator, Callable
from typing import Any, TypeGuard

from ozobot.webrtc.exceptions import QueueReaderConcurrentUseNotSupportedError, QueueReaderNotEnteredError


class QueueReader[T]:
    _event_queue: Queue[T]
    _entered: bool

    def __init__(self, queue: Queue[T]):
        self._event_queue = queue
        self._entered = False

    async def __aenter__(self) -> typing.Self:
        if self._entered:
            raise QueueReaderConcurrentUseNotSupportedError()
        self._entered = True

        return self

    async def __aexit__(self, *exc: Any) -> None:
        self._entered = False

    async def close(self) -> None:
        self._event_queue.shutdown(immediate=True)

    async def items(self) -> AsyncIterator[T]:
        """Iterates through items in the queue"""
        if not self._entered:
            raise QueueReaderNotEnteredError()

        while True:
            try:
                value = await self._event_queue.get()
            except QueueShutDown:
                return

            yield value

    async def wait_until(self, rule: Callable[[Any], TypeGuard[T]]) -> T | None:
        """Reads items from the queue until `rule(item)` is `True`"""
        if not self._entered:
            raise QueueReaderNotEnteredError()

        async for event in self.items():
            if rule(event):
                return event

        return None


def get_unused_tcp_port() -> int:
    with contextlib.closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(("localhost", 0))
        return int(s.getsockname()[1])
