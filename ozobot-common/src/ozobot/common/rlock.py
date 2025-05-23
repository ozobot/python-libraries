import asyncio


class RLock:
    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._lock_owner: asyncio.Task | None = None
        self._counter = 0

    async def __aenter__(self) -> None:
        if not self._counter or self._lock_owner != asyncio.current_task():
            await self._lock.acquire()
            self._lock_owner = asyncio.current_task()

        self._counter += 1

    async def __aexit__(self, *args) -> bool:
        if self._counter == 1:
            self._lock.release()
            self._lock_owner = None

        self._counter -= 1

        return False

    def locked(self) -> bool:
        return self._lock.locked()

    def owned(self) -> bool:
        return self._lock.locked() and self._lock_owner == asyncio.current_task()
