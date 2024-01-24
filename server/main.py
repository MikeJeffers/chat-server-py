import asyncio
import websockets
import logging
import db
import json
import tokens
logger = logging.getLogger('websockets')
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())

psql = db.db()

users = {}
messages = []


def try_parse(raw: str) -> tuple:
    try:
        data = json.loads(raw)
        command = data.get("command")
        if command:
            return command, data
    except Exception:
        return None, None


async def send(websocket: websockets.WebSocketClientProtocol, command: str, data: dict | None):
    payload = {"command": command}
    if data:
        payload.update(data)
    await websocket.send(json.dumps(payload))


async def authConnection(websocket: websockets.WebSocketClientProtocol):
    try:
        # We assume the data recv'd is an auth command with token
        # any violation in these assertions will bail and close the connection
        raw = await websocket.recv()
        print(f"<<< {raw}")
        command, data = try_parse(raw)
        if not data or not command:
            Exception("Bad data payload")
        token = data.get("token")
        if not token:
            Exception("Bad data payload")

        verified = tokens.check_token(token)
        print(token, "->", verified)
        if not verified:
            Exception("token verification failed")
        await handleChat(websocket)
    except Exception as e:
        return None


async def handleChat(websocket: websockets.WebSocketClientProtocol):
    while websocket.open:
        try:
            raw = await websocket.recv()
            command, data = try_parse(raw)
            if not data or not command:
                Exception("Bad data payload")

            response = f"Server received command {command}!"

            await websocket.send(response)
            await asyncio.sleep(0)
            print(f">>> {response}")
        except websockets.ConnectionClosed as e:
            logging.warning("socket closed")
        except Exception as e2:
            print(e2)
            await send(websocket, "ERROR", {"message": str(e2)})


async def main():
    async with websockets.serve(authConnection, "localhost", 8765):
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    asyncio.run(main(), debug=True)
