import typing


class RpcCallReentryError(Exception):
    def __init__(self):
        super().__init__("Cannot RPC call cannot be reentered or called again")
        

class RpcCall[TResponse, TEvent]:
    def __init__(self, response: typing.AsyncGenerator[TResponse, TEvent]) -> None:
        self._response = response
        self._used = False

    def __await__(self) -> typing.Generator[None, None, TResponse]:
        if self._used:
            raise RpcCallReentryError()
        
        self._used = True
        async def x():
            pass
        
        return self._get_response_and_close().__await__()

    async def _get_response_and_close(self) -> TResponse:
        response = await anext(self._response)
        await self._response.aclose()
        return response
        
    async def __aenter__(self) -> tuple[TResponse, typing.AsyncIterator[TEvent]]:
        if self._used:
            raise RpcCallReentryError()

        self._used = True

        response = await anext(self._response)
        return response, self._response

    async def __aexit__(self, *args, **kwargs) -> None:
        await self._response.aclose()
        
