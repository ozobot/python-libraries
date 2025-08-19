import pytest
from ozobot.common.exceptions import OzobotError


def test_exception():
    with pytest.raises(OzobotError) as raised:
        raise OzobotError("Something bad happened")

    assert raised.value.args == ("Something bad happened",)
    assert raised.value.context == {}
    assert str(raised.value) == "Something bad happened"
    assert repr(raised.value) == 'OzobotError("Something bad happened")'


def test_exception_context():
    with pytest.raises(OzobotError) as raised:
        try:
            ex = OzobotError("Something bad happened")
            ex.add_context("bot_name", "bot1234")
            raise ex
        except OzobotError as err:
            err.add_context("ip_address", "1.2.3.4")
            raise err

    assert raised.value.args == ("Something bad happened",)
    assert raised.value.context == {"bot_name": "bot1234", "ip_address": "1.2.3.4"}
    assert str(raised.value) == ("Something bad happened\nbot_name=bot1234\nip_address=1.2.3.4")
    assert (
        repr(raised.value)
        == 'OzobotError("Something bad happened", context={"bot_name": "bot1234", "ip_address": "1.2.3.4"})'
    )
