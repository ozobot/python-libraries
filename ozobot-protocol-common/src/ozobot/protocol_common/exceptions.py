class OzobotProtocolCommandError(Exception):
    def __init__(
        self, command: str, return_value: str, *, description: str | None = None
    ) -> None:
        if description:
            details = f"(returned: {return_value}, description: {description})"
        else:
            details = f"({return_value})"

        super().__init__(f"Protocol command failed: {command} {details}")
