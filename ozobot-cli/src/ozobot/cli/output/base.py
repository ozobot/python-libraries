from __future__ import annotations

import typing


class OutputFormatter(typing.Protocol):
    async def __aenter__(self) -> OutputFormatter: ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: typing.Any,
    ) -> None: ...

    async def emit(self, data: dict[str, typing.Any]) -> None: ...
