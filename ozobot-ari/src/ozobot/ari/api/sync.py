from ozobot.ari.api.core import Ari
from ozobot.common.sync import as_sync
from ozobot.linefollower.api.sync import SyncLineFollower, SyncMemoryRegions
from ozobot.linefollower.datatypes import Direction, NamedColor


class SyncAriVirtualMemory(SyncMemoryRegions): ...


class SyncAri(SyncLineFollower):
    @property
    def data(self) -> SyncAriVirtualMemory:
        """
        Robot sensors.

        Contains virtual memory and sensor structures allowing a subset of read, write and watch methods.
        """

        return SyncAriVirtualMemory(self._ari)

    def __init__(self, ari: Ari) -> None:
        self._ari = ari
        super().__init__(ari)

    @as_sync
    async def user_io_print(self, message: str) -> None:
        """
        Display a temporary text message.

        A popup is shown on the Ari screen for a few moments. Does only block until the popup is shown.

        :param message: Message text

        .. code-block:: python

            robot.user_io_print("Hello world!")
        """
        await self._ari.user_io_print(message)

    @as_sync
    async def user_io_alert(self, message: str, *, cancellable: bool = False) -> None:
        """
        Display a text message requiring confirmation.

        A text message with a button to confirm is shown. The function blocks until the message is confirmed.

        Optionally, the message can be made cancellable. Cancelling the message results in `asyncio.CancelledError` being raised.

        :param message: Message text
        :param cancellable: If true, the message can also be cancelled

        :raises asyncio.CancelledError: Raised when a cancellable message gets cancelled.

        .. code-block:: python

            import asyncio

            # move after after user confirmation
            robot.user_io_alert("Waiting for confirmation!")
            robot.move(100, 50)

            # move after confirmation or skip the movement by cancelling
            try:
                robot.user_io_alert("Waiting for confirmation!", cancellable=True)
                move = True
            except asyncio.CancelledError:
                move = False

            if move:
                robot.move(100, 50)
            else:
                print("Movement skipped")
        """
        await self._ari.user_io_alert(message, cancellable=cancellable)

    @as_sync
    async def user_io_prompt[T: (str, float, int, bool, NamedColor, Direction)](
        self, message: str, _type: type[T], options: list[T], *, cancellable: bool = False
    ) -> T:
        """
        Display a selection dialog.

        A text message along a list of options of the same type is displayed on the screen allowing user to select a single value. The selected
        value is returned by the function. Blocks until a selection is made.

        Optionally, the dialog can be made cancellable. Cancelling the dialog results in `asyncio.CancelledError` being raised.

        :param message: Message text
        :param _type: Type of the items in the option list
        :param options: A list of options to choose from
        :param cancellable: If true, the message can also be cancelled

        :raises asyncio.CancelledError: Raised when a cancellable message gets cancelled.
        :return: Selected value, the type is the same as the :obj:`_type` argument

        .. warning::
            Types cannot be combined, so for example, you cannot choose between `"Hello"`, `2` and `Direction.LEFT`. You can workaround this by using strings.

        .. code-block:: python

            from ozobot.linefollower import Direction, NamedColor

            # select direction
            dir = robot.user_io_prompt("Select direction", Direction, [Direction.LEFT, Direction.RIGHT])
            print(dir)  # prints either Direction.LEFT or Direction.RIGHT depending on what the user selected

            # select color
            color = robot.user_io_prompt("Select color", NamedColor, [NamedColor.BLACK, NamedColor.WHITE, NamedColor.BLUE])
            print(color)  # prints one of the colors depending on what the user selected


            # select a number
            num = robot.user_io_prompt("Select a number", int, list(range(5)))
            print(num)  # prints number 0 - 4 depending on what the user selected

            # types cannot be combined, this would fail
            # selection = robot.user_io_primpt("Select", float, ["hello", 2, Direction.LEFT])
        """
        return await self._ari.user_io_prompt(message, _type, options, cancellable=cancellable)
