from __future__ import annotations

import typing


def _truncate(value: str, width: int) -> str:
    if len(value) <= width:
        return value
    return value[: width - 1] + "\u2026"


class TableFormatter:
    def __init__(self, stream: typing.TextIO, *, keys: typing.Sequence[str], column_size: typing.Sequence[int]) -> None:
        self._stream = stream
        self._keys = keys
        self._column_size = column_size

    async def __aenter__(self) -> TableFormatter:
        header = "\t".join([f"{k.upper():<{s}}" for k, s in zip(self._keys, self._column_size, strict=True)])
        print(header, file=self._stream)
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: typing.Any,
    ) -> None:
        return None

    async def emit(self, data: dict[str, typing.Any]) -> None:
        fields = []

        for k in self._keys:
            fields.append(data[k] if data[k] is not None else "-")

        print(
            "\t".join(f"{f:<{s}}" for f, s in zip(fields, self._column_size, strict=True)),
            file=self._stream,
        )
