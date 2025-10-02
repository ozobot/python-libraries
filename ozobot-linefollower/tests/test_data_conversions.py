import datetime

from ozobot.linefollower.conversions import sample_from_protocol
from ozobot.linefollower.datatypes import Sample


def test_sample_from_protocol() -> None:
    class _Data:
        def __init__(self, val1: int, val2: int) -> None:
            self.val1 = val1
            self.val2 = val2
            self.timestamp = 1

    sample = sample_from_protocol(_Data(1, 2), lambda d: d.val1 + d.val2)

    assert isinstance(sample, Sample)
    assert sample.value == 3
    assert sample.timestamp == datetime.datetime.fromtimestamp(1)
