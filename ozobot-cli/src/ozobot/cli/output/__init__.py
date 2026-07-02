from __future__ import annotations

import typing

from .base import OutputFormatter
from .json import JsonFormatter
from .table import TableFormatter


def make_formatter(*, json_output: bool, stream: typing.TextIO, keys: typing.Sequence[str], column_size: typing.Sequence[int]) -> OutputFormatter:
    if json_output:
        return JsonFormatter(stream)
    return TableFormatter(stream, keys=keys, column_size=column_size)


__all__ = ["JsonFormatter", "OutputFormatter", "TableFormatter", "make_formatter"]
