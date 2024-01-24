import asyncio
import datetime
import websockets
import logging
import db
import json
import tokens
logger = logging.getLogger('websockets')
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())

psql = db.db()
connections = set()
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


def broadcast(command: str, data: dict | None):
    payload = {"command": command}
    if data:
        payload.update(data)
    message = json.dumps(payload)
    websockets.broadcast(connections, message)


def add_user(user: dict, websocket: websockets.WebSocketClientProtocol):
    connections.add(websocket)
    users[user.get("id")] = user
    broadcast("USER_JOIN", {"user":{"name": user.get(
        "username"), "id": user.get("id")}})


def remove_user(id: int, websocket: websockets.WebSocketClientProtocol):
    if websocket in connections:
        connections.remove(websocket)
    if not id in users:
        return False
    data = users[id]
    broadcast("USER_LEAVE", {"user":{"name": data.get(
        "username"), "id": data.get("id")}})
    del users[id]
    return True


def get_all_users():
    return [{"id": u.get("id"), "name": u.get("username")} for _, u in users.items()]


def add_message(content, user):
    message = {"message": content, "from": user.get(
        "username"), "at": datetime.datetime.utcnow().isoformat()+"Z"}
    messages.append(message)
    if len(messages) > 10:
        messages.pop(0)
    broadcast("MESSAGE_ADD", {"message":message})


async def authConnection(websocket: websockets.WebSocketClientProtocol):
    try:
        # We assume the data recv'd is an auth command with token
        # any violation in these assertions will bail and close the connection
        raw = await websocket.recv()
        command, data = try_parse(raw)
        if not data or not command:
            raise Exception("Bad data payload")
        token = data.get("token")
        if not token:
            raise Exception("Bad data payload")

        verified = tokens.check_token(token)
        if not verified or not verified.get("id"):
            raise Exception("token verification failed")
        user = db.get_user(verified.get("id"), psql)
        if not user or "id" not in user or "username" not in user:
            raise Exception("user lookup failed")
        add_user(user, websocket)
        await send(websocket, "ACK", {"messages": messages, "users": get_all_users()})
        await handleChat(websocket, user)
    except Exception as e:
        logger.exception(e)
        return None


async def handleChat(websocket: websockets.WebSocketClientProtocol, user: dict):
    while websocket.open:
        try:
            raw = await websocket.recv()
            command, data = try_parse(raw)
            if not data or not command:
                raise Exception("Bad data payload")

            if command == "SEND_MESSAGE":
                add_message(data.get("message"), user)
            elif command == "REFRESH":
                await send(websocket, "ACK", {"messages": messages, "users": get_all_users()})
            else:
                logging.warning("Unsupported command %s", command)
        except Exception as e2:
            await send(websocket, "ERROR", {"message": str(e2)})
    # After loop
    remove_user(user.get("id"), websocket)


async def main():
    stop = asyncio.Future()
    server = await websockets.serve(authConnection, "0.0.0.0", 8078)
    await stop
    await server.close()

if __name__ == "__main__":
    asyncio.run(main())
