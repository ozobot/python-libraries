import typing


class RpcCallReentryError(Exception):
    def __init__(self):
        super().__init__("Cannot RPC call cannot be reentered or called again")
        

class RpcCall[TResponse, TEvent]:
    def __init__(self, iterator: typing.AsyncGenerator[TResponse | TEvent, None]) -> None:
        self._iterator = iterator
        self._used = False

    def __await__(self) -> TResponse:
        if self._used:
            raise RpcCallReentryError()
        
        self._used = True
        return anext(self._iterator).__await__()
        
    async def __aenter__(self) -> typing.AsyncIterator[TEvent]:
        if self._used:
            raise RpcCallReentryError()

        self._used = True
        return self._iterator

    async def __aexit__(self, *args, **kwargs) -> None:
        await self._iterator.aclose()
