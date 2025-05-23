import typing


class RpcCallReentryError(Exception):
    def __init__(self):
        super().__init__("Cannot RPC call cannot be reentered or called again")


class RpcCall[TResponse, TEvent]:
    def __init__(
        self,
        rpc: typing.AsyncContextManager[tuple[TResponse, typing.AsyncGenerator[TEvent, None]]],
    ) -> None:
        self._rpc = rpc
        self._used = False

    def __await__(self) -> typing.Generator[None, None, TResponse]:
        if self._used:
            raise RpcCallReentryError()

        self._used = True

        async def x():
            pass

        return self._get_response_and_close().__await__()

    async def _get_response_and_close(self) -> TResponse:
        async with self._rpc as (resp, _):
            return resp

    async def __aenter__(self) -> tuple[TResponse, typing.AsyncIterator[TEvent]]:
        if self._used:
            raise RpcCallReentryError()

        self._used = True

        response, events = await self._rpc.__aenter__()
        return response, events

    async def __aexit__(self, *args, **kwargs) -> None:
        await self._rpc.__aexit__(*args, **kwargs)
