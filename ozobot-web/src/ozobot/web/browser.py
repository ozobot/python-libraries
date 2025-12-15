import typing

from loguru import logger

try:
    # this library is only present in web-python web application distribution
    # if the import fails, we are running natively, and we can create a mock function instead
    from _ozo import _rpcCoroutine  # type: ignore[import]

except ImportError:
    logger.warning(
        "`_ozo` module could not be imported which is expected to happen when a web driver is used outside of the pyodide environment"
    )

    async def _rpcCoroutine(object_name: str, func_name: str, args: list[typing.Any]) -> typing.Any:
        raise NotImplementedError("`_rpcCoroutine` is only available in the pyodide environment")
