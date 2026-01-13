import typing

from ozobot.evo.exceptions import EvoFileNotFound, OzobotProtocolCommandError
from ozobot.evo.protocol import Types


class _HasExecutionState(typing.Protocol):
    executionState: Types.ExecutionStateEnum


@typing.runtime_checkable
class _HasCallStatus(typing.Protocol):
    callStatus: Types.CallStatus


@typing.runtime_checkable
class _HasResult(typing.Protocol):
    result: Types.IOResult


def handle_response(function_name: str, response: _HasCallStatus | _HasResult) -> None:
    if isinstance(response, _HasCallStatus):
        if response.callStatus != Types.CallStatus.CallSuccess:
            raise OzobotProtocolCommandError(function_name, response.callStatus.name, description="call failed")
    elif isinstance(response, _HasResult):
        if response.result != Types.IOResult.Success:
            raise OzobotProtocolCommandError(function_name, response.result.name, description="call failed")


async def handle_events[T: _HasExecutionState](function_name: str, events: typing.AsyncIterator[T]) -> T:
    """Checks event execution state and returns an event confirming event success. Raises exception otherwise."""
    async for event in events:
        if event.executionState == Types.ExecutionStateEnum.FinishedNormal:
            return event

        if event.executionState == Types.ExecutionStateEnum.FileNotFound:
            raise EvoFileNotFound()

        if event.executionState != Types.ExecutionStateEnum.Running:
            raise OzobotProtocolCommandError(
                function_name,
                event.executionState.name,
                description="failure execution state",
            )

    raise OzobotProtocolCommandError(function_name, "empty", description="no command end state received")
