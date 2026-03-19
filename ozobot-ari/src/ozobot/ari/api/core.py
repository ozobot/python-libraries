import typing

from ozobot.ari.driver import AriDriver
from ozobot.linefollower.api.core import LineFollower
from ozobot.linefollower.datatypes import Direction, NamedColor, Sample, TimeOfFlight
from ozobot.linefollower.driver.interface import VirtualMemoryRegions, WatchableRegion


class AriVirtualMemory(VirtualMemoryRegions, typing.Protocol):
    @property
    def time_of_flight(self) -> WatchableRegion[Sample[TimeOfFlight]]:
        """
        Distance measurement based on Time-of-Flight sensor.
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

        A popup is shown on the Ari screen for a few seconds. Only blocks while the popup is shown.

        :param message: Message text

        .. code-block:: python

            await robot.user_io_print("Hello world!")
        """

        await self._ari_driver.user_io_print(message)

    async def user_io_alert(self, message: str, *, cancellable: bool = False) -> None:
        """
        Display a text message requiring confirmation.

        A text message with a button to confirm is shown on the Ari screen. The function blocks until the message is confirmed.

        Optionally, the message can be made cancellable, so that the user can dismiss it on the Ari screen. Cancelling the message results in `asyncio.CancelledError` being raised.

        :param message: Message text
        :param cancellable: If true, the message can also be cancelled by the user

        :raises asyncio.CancelledError: Raised when a cancellable message gets cancelled by the user.

        .. code-block:: python

            import asyncio

            # move after after user confirmation
            await robot.user_io_alert("Waiting for confirmation!")
            await robot.move(100, 50)

            # move after confirmation or skip the movement by cancelling
            try:
                await robot.user_io_alert("Waiting for confirmation!", cancellable=True)
                move = True
            except asyncio.CancelledError:
                move = False

            if move:
                await robot.move(100, 50)
            else:
                print("Movement skipped")
        """

        await self._ari_driver.user_io_alert(message, cancellable=cancellable)

    async def user_io_prompt[T: (str, float, int, bool, NamedColor, Direction)](
        self, message: str, _type: type[T], options: list[T], *, cancellable: bool = False
    ) -> T:
        """
        Display a selection dialog.

        A text message along a list of options of the same type is displayed on the Ari screen, allowing the user to select a single value. The selected
        value is returned by the function. Blocks until a selection is made.

        Optionally, the dialog can be made cancellable, so that the user can dismiss it on the Ari screen. Cancelling the dialog results in `asyncio.CancelledError` being raised.

        :param message: Message text
        :param _type: Type of the items in the option list
        :param options: A list of options to choose from
        :param cancellable: If true, the message can also be cancelled by the user

        :raises asyncio.CancelledError: Raised when a cancellable message gets cancelled by the user.
        :return: Selected value, the type is the same as the :obj:`_type` argument

        .. warning::
            Types cannot be combined, so for example, you cannot choose between `"Hello"`, `2` and `Direction.LEFT`. You can workaround this by using strings.

        .. code-block:: python

            from ozobot.linefollower import Direction, NamedColor

            # select a direction
            dir = await robot.user_io_prompt("Select a direction", Direction, [Direction.LEFT, Direction.RIGHT])
            print(dir)  # prints either Direction.LEFT or Direction.RIGHT depending on what the user selected

            # select a color
            color = await robot.user_io_prompt("Select a color", NamedColor, [NamedColor.BLACK, NamedColor.WHITE, NamedColor.BLUE])
            print(color)  # prints one of the colors depending on what the user selected

            # select a number. Float type is also supported.
            num = await robot.user_io_prompt("Select a number", int, list(range(5)))
            print(num)  # prints number 0 - 4 depending on what the user selected

            # select a string
            string = await robot.user_io_prompt("Select a string", str, ["Option 1", "Option 2"])
            print(string)  # prints "Option 1" or "Option 2"

            # types cannot be combined, this would fail
            # selection = await robot.user_io_prompt("Select", float, ["hello", 2, Direction.LEFT])
        """

        return await self._ari_driver.user_io_prompt(message, _type, options, cancellable=cancellable)
