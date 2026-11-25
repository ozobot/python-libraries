from __future__ import annotations

import typing
import contextlib

from ozobot.common.exceptions import OzobotError
from ozobot.linefollower.api.data_access import WatcherOutputContainer


async def get_next_event[T](
    watcher: contextlib.AbstractAsyncContextManager[WatcherOutputContainer[T]],
) -> T:
    async with watcher as container:
        return await anext(aiter(container))


class UserError(OzobotError):
    pass
