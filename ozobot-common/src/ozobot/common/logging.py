import logging
import sys
import typing

from loguru import logger

_debug_logger_format = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
    "- <level>{message} {extra}</level>"
)


def setup_logging(level: typing.Literal["TRACE", "DEBUG", "INFO", "SUCCESS", "WARNING", "ERROR", "CRITICAL"]):
    logging.basicConfig(handlers=[_InterceptHandler()], level=0)

    logger.remove(0)
    logger.add(sys.stderr, level=level, format=_debug_logger_format, backtrace=True, diagnose=True)


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
