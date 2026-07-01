import typing

from ozobot.ari.protocol import base, memread, memwrite, notification, request, response
from ozobot.jsonrpc.executor import Method

MOVE_STRAIGHT = Method(
    request=request.MoveStraightRequest,
    response=response.MoveStraightResponse,
    notification=notification.MotionNotification,
)

ROTATE = Method(
    request=request.RotateRequest,
    response=response.RotateResponse,
    notification=notification.MotionNotification,
)

VELOCITY = Method.without_notifications(
    request=request.VelocityRequest,
    response=response.VelocityResponse,
)

LINE_NAVIGATION = Method(
    request=request.LineNavigationRequest,
    response=response.LineNavigationResponse,
    notification=notification.LineNavigationNotification,
)

SET_LED = Method.without_notifications(
    request=request.SetLEDRequest,
    response=response.SetLEDResponse,
)

PLAY_TONE = Method.without_notifications(
    request=request.PlayToneRequest,
    response=response.PlayToneResponse,
)

PLAY_SOUND = Method.without_notifications(
    request=request.PlaySoundRequest,
    response=response.PlaySoundResponse,
)

TIME_OF_FLIGHT = Method.without_response(
    request=request.TimeOfFlightRequest,
    notification=notification.TimeOfFlightNotification,
)

USER_IO_PRINT = Method.without_notifications(
    request=request.UserIoPrintRequest,
    response=response.UserIoPrintResponse,
)

USER_IO_ALERT = Method.without_notifications(
    request=request.UserIoAlertRequest,
    response=response.UserIoAlertResponse,
)

USER_IO_PROMPT = Method.without_notifications(
    request=request.UserIoPromptRequest,
    response=response.UserIoPromptResponse,
)

HEALTH_CHECK = Method.without_notifications(
    request=request.HealthCheckRequest,
    response=response.HealthCheckResponse,
)


MEM_READ = Method.without_notifications(
    request=memread.MemReadRequest,
    response=memread.MemReadResponse,
)

MEM_WRITE = Method.without_notifications(
    request=memwrite.MemWriteRequest,
    response=memwrite.MemWriteResponse,
)

WATCH = Method.without_response(
    request=memread.WatchRequest,
    notification=memread.WatchNotification,
)

REQUEST_METHODS = {
    typing.cast(type[base.Request], m.request): typing.cast(Method[base.Request, base.Response, base.Notification], m)
    for m in (
        MOVE_STRAIGHT,
        ROTATE,
        VELOCITY,
        LINE_NAVIGATION,
        SET_LED,
        PLAY_TONE,
        PLAY_SOUND,
        TIME_OF_FLIGHT,
        USER_IO_PRINT,
        USER_IO_ALERT,
        USER_IO_PROMPT,
        HEALTH_CHECK,
        MEM_READ,
        MEM_WRITE,
        WATCH,
    )
}
