import typing

from ozobot.ari.driver import AriDriver
from ozobot.linefollower.api.core import LineFollower
from ozobot.linefollower.datatypes import ClassifiedColor, Direction, Sample, TimeOfFlight
from ozobot.linefollower.driver.interface import VirtualMemoryRegions, WatchableRegion


class AriVirtualMemory(VirtualMemoryRegions, typing.Protocol):
    @property
    def time_of_flight(self) -> WatchableRegion[Sample[TimeOfFlight]]:
        """
        Time of flight based distance measurement.
        """


# this enables verbose errors when memory region implementations do not
# match the interfaces
if typing.TYPE_CHECKING:
    _vm: AriVirtualMemory
    from ozobot.ari.driver.native import NativeMemoryRegions
    from ozobot.ari.driver.web import AriWebMemoryRegions

    _vm = AriWebMemoryRegions()  # type: ignore[call-arg]
    _vm = NativeMemoryRegions()  # type: ignore[call-arg]


class Ari(LineFollower):
    @property
    def data(self) -> AriVirtualMemory:
        return self._ari_driver.memory

    def __init__(self, driver: AriDriver) -> None:
        super().__init__(driver)
        self._ari_driver = driver

    async def user_io_print(self, message: str) -> None:
        """
        Display a temporary text message.

        A popup is shown on the Ari screen for a few moments. Does only block until the popup is shown.

        :param message: Message text
        """

        await self._ari_driver.user_io_print(message)

    async def user_io_alert(self, message: str, *, cancellable: bool = False) -> None:
        """
        Display a text message requiring confirmation.

        A text message with a button to confirm is shown. The function blocks until the message is confirmed.

        Optionally, the message can be made cancellable. Cancelling the message results in `asyncio.CancelledError` being raised.

        :param message: Message text
        :param cancellable: If true, the message can also be cancelled

        :raises asyncio.CancelledError: Raised when a cancellable message gets cancelled.
        """

        await self._ari_driver.user_io_alert(message, cancellable=cancellable)

    async def user_io_prompt[T: (str, float, int, bool, ClassifiedColor, Direction)](
        self, message: str, _type: type[T], options: list[T], *, cancellable: bool = False
    ) -> T:
        """
        Display a selection dialog.

        A text messsage along a list of options of the same type is displayed on the screen allowing user to select a single value. The selected
        value is returned by the function. Blocks until a selection is made.

        Optionally, the dialog can be made cancellable. Cancelling the dialog results in `asyncio.CancelledError` being raised.

        :param message: Message text
        :param _type: Type of the items in the option list
        :param options: A list of options to choose from
        :param cancellable: If true, the message can also be cancelled

        :raises asyncio.CancelledError: Raised when a cancellable message gets cancelled.
        :return: Selected value, the type is the same as the :obj:`_type` argument
        """

        return await self._ari_driver.user_io_prompt(message, _type, options, cancellable=cancellable)
