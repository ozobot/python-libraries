from dataclasses import dataclass


@dataclass(frozen=True, kw_only=True)
class BaseHandle:
    """
    Factory class for obtaining robot connection.

    The instance of this class holds connection filters that describe which robot to connect to. If multiple selectors are
    specified, everyone has to match the same robot. Selector that are not defined (or set to None) are ignored.

    The native Python library only supports WebRTC transport. BLE is only used for scanning and acquiring the connection key.

    Only :py:attr:`name` selector is supported in Web Python.
    """

    address: str | None = None
    """
    BLE MAC address of the robot.

    Accepts wildmark '*' character that matches any string.
    """

    id: str | None = None
    """
    Robot ID.

    Accepts wildmark '*' character that matches any string.
    """

    name: str | None = None
    """
    Robot BLE name.

    Accepts wildmark '*' character that matches any string.
    """
