from builtins import NotImplementedError
import pytest
import os


@pytest.mark.skipif("CI" not in os.environ, reason="Can only be run on CI with a broker set up")
def test_open_channel() -> None:
    raise NotImplementedError()


@pytest.mark.skipif("CI" not in os.environ, reason="Can only be run on CI with a broker set up")
def test_send_receive() -> None:
    raise NotImplementedError()


@pytest.mark.skipif("CI" not in os.environ, reason="Can only be run on CI with a broker set up")
def test_reply_to() -> None:
    raise NotImplementedError()
