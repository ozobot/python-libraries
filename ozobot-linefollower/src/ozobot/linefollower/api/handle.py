class BaseHandle:
    """
    Factory class for obtaining robot connection.

    Instance of this class can be used as a context manager to open a connection to robot given by the connection filters given on initialization. If multiple selectors are
    specified, each one has to match to select the robot. Selectors that are not defined (or set to None) are ignored.

    .. note::
        The behavior is platform-specific and only :py:attr:`name` selector is supported in the web Ozobot Editor.
    """

    def __init__(self, *, address: str | None = None, id: str | None = None, name: str | None = None) -> None:
        self._address = address
        self._id = id
        self._name = name

    @property
    def address(self) -> str | None:
        """
        BLE MAC address of the robot.

        Accepts wildcard '*' character that matches any string.
        """
        return self._address

    @property
    def id(self) -> str | None:
        """
        Robot ID.

        Accepts wildcard '*' character that matches any string.
        """
        return self._id

    @property
    def name(self) -> str | None:
        """
        Robot BLE name.

        Accepts wildcard '*' character that matches any string.
        """
        return self._name
