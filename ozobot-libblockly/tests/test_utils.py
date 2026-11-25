from unittest.mock import Mock

from ozobot.libblockly.utils import get_next_event


async def test_get_next_event() -> None:
    sample_sets = iter(
        [
            [1, 2],
            [3, 4],
        ]
    )

    async def _watcher_aiter(*args):
        samples = next(sample_sets)
        for s in samples:
            yield s

    async def _watcher_aenter(*args):
        return _watcher_aiter()

    async def _watcher_aexit(*args):
        pass

    watcher_mock = Mock(__aenter__=_watcher_aenter, __aexit__=_watcher_aexit)
    ret = await get_next_event(watcher_mock)
    assert ret == 1

    ret = await get_next_event(watcher_mock)
    assert ret == 3
