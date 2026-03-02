import logging
import sys
import typing

from loguru import logger as _logger

if typing.TYPE_CHECKING:
    from loguru import Record
else:
    Record = dict


def format_extra(record: Record):
    extra = record.get("extra", {})
    kwargs = {k: v for k, v in extra.items() if not k.startswith("_")}

    if kwargs:
        formatted_kwargs = " ".join(f"{k}={v!r}" for k, v in kwargs.items())
        new_message = "\t".join([record["message"], formatted_kwargs])
        record["message"] = new_message


logger = _logger.patch(format_extra)


def hook_native_logger_interceptor():
    logging.basicConfig(handlers=[_InterceptHandler()], level=0)


class _InterceptHandler(logging.Handler):
    def emit(self, record):
        # Get corresponding Loguru level if it exists.
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message.
        frame, depth = sys._getframe(6), 6
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())
