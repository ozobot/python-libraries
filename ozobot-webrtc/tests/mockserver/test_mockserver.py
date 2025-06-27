import websockets

from .mockserver import MockWebSocketServer


async def test_mock_server():
    async with MockWebSocketServer("localhost", 1234).serve() as server:
        async with websockets.connect(server.url) as client:
            await server.send_to_client("hello")
            from_server = await client.recv()
            await client.send("hi!")
            from_client = await server.read_received_from_client()

        assert from_server == "hello"
        assert from_client == "hi!"
