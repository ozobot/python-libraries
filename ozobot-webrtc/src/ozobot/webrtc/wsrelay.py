import asyncio
import contextlib
from collections.abc import AsyncIterator
from typing import Self

import websockets
from loguru import logger
from websockets.legacy.client import WebSocketClientProtocol
from yarl import URL


class WebSocketRelay:
    _remote_uri: URL
    _local_port: int
    num_active_handlers: int

    def __init__(self, remote_uri: URL, local_port: int):
        self._remote_uri = remote_uri
        self._local_port = local_port
        self.num_active_handlers = 0

    @contextlib.asynccontextmanager
    async def serve(self) -> AsyncIterator[Self]:
        logger.info("WebSocket relay started")

        server = await asyncio.start_server(self._server_cbk, port=self._local_port)
        with contextlib.closing(server):
            yield self

    @logger.catch(reraise=True)
    async def _server_cbk(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        logger.info("Handler created")
        self.num_active_handlers += 1
        try:
            async with websockets.connect(str(self._remote_uri)) as client, asyncio.TaskGroup() as tg:
                coros = [
                    self._remote_to_local(client, writer),
                    self._local_to_remote(client, reader, writer),
                    writer.wait_closed(),
                ]
                tasks = [tg.create_task(coro) for coro in coros]
                _, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
                for p in pending:
                    p.cancel()
        finally:
            logger.info("Handler closed")
            writer.write_eof()
            self.num_active_handlers -= 1

    async def _local_to_remote(
        self, client: WebSocketClientProtocol, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        try:
            while not reader.at_eof():
                data = await reader.read(1024)
                if data:
                    await client.send(data)

            logger.debug("Closing handler on reader EOF (TCP side initiated close)")
        finally:
            writer.write_eof()

    async def _remote_to_local(self, client: WebSocketClientProtocol, writer: asyncio.StreamWriter) -> None:
        try:
            async for msg in client:
                if writer.is_closing():
                    return
                writer.write(msg if isinstance(msg, bytes) else bytes(msg, "utf8"))

            logger.debug("Closing handler on client closing (WebSocket side initiated close)")
        finally:
            writer.write_eof()
