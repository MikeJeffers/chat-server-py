import asyncio
import websockets
import logging
logger = logging.getLogger('websockets')
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())

async def hello(websocket:websockets.WebSocketClientProtocol):
    while websocket.open:
        try:
            name = await websocket.recv()
            print(f"<<< {name}")

            greeting = f"Hello {name}!"

            await websocket.send(greeting)
            print(f">>> {greeting}")
        except websockets.ConnectionClosed as e:
            logging.warning("socket closed")


async def main():
    async with websockets.serve(hello, "localhost", 8765):
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    asyncio.run(main(), debug=True)