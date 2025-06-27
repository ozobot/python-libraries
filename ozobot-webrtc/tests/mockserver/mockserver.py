import asyncio
import contextlib
from typing import AsyncIterator, Self

from loguru import logger
from websockets.legacy.server import WebSocketServerProtocol, serve


class MockWebSocketServer:
    _host: str
    _port: int
    _server_used: bool

    _queue_from_client: asyncio.Queue[str]
    _queue_to_client: asyncio.Queue[str]

    @property
    def url(self) -> str:
        return f"ws://{self._host}:{self._port}"

    def __init__(self, host: str, port: int):
        self._host = host
        self._port = port
        self._server_used = False

        self._queue_from_client = asyncio.Queue()
        self._queue_to_client = asyncio.Queue()

    @contextlib.asynccontextmanager
    async def serve(self) -> AsyncIterator[Self]:
        async with serve(self._mock_websocket_server_handler, self._host, self._port):
            yield self

    async def read_received_from_client(self) -> str:
        return await self._queue_from_client.get()

    async def send_to_client(self, message: str) -> None:
        await self._queue_to_client.put(message)

    @contextlib.asynccontextmanager
    async def _claim_server(self):
        assert not self._server_used, "Server already has a client connected"
        self._server_used = True
        yield
        self._server_used = False

    async def _mock_websocket_server_handler(self, protocol: WebSocketServerProtocol) -> None:
        logger.debug("Mock server handler triggered")
        async with self._claim_server(), asyncio.TaskGroup() as tg:
            logger.debug("Starting tasks")
            reader_task = tg.create_task(self._reader(protocol))
            writer_task = tg.create_task(self._writer(protocol))
            await protocol.wait_closed()
            logger.debug("Stopping tasks")
            reader_task.cancel()
            writer_task.cancel()

    async def _reader(self, protocol: WebSocketServerProtocol):
        logger.debug("Started reader task")
        async for message in protocol:
            logger.debug("Received message from client", message=message)
            await self._queue_from_client.put(message if isinstance(message, str) else message.decode("utf8"))

    async def _writer(self, protocol: WebSocketServerProtocol):
        logger.debug("Started writer task")
        while True:
            message = await self._queue_to_client.get()
            logger.debug("Sending message to client", message=message)
            await protocol.send(message)

    def close(self) -> None:
        self._queue_from_client.shutdown(immediate=True)
        self._queue_to_client.shutdown(immediate=True)
