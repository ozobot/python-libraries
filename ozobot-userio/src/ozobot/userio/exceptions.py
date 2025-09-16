from ozobot.common.exceptions import OzobotError


class UserIoError(OzobotError): ...


class UnexpectedUserIoPromptOptionTypeError(UserIoError):
    def __init__(self, option: object, _type: type) -> None:
        super().__init__(
            f"Unexpected user io prompt option: '{option}' has type '{type(option)!r}' but '{_type!r}' expected"
        )


class UnexpectedUserIoPromptResponseReceivedError(UserIoError):
    def __init__(self, value: object, _type: type) -> None:
        super().__init__(
            f"Unexpected user io prompt response received: {value} has type {type(value)!r} but '{_type!r}' expected"
        )


class UnexpectedUserIoPromptTypeError(UserIoError):
    def __init__(self, _type: type) -> None:
        super().__init__(f"Unexpected user io prompt type given: {_type!r}")
