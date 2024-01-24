import redis
import os
import jwt
from dotenv import load_dotenv
from datetime import timedelta

load_dotenv()

HOST = os.getenv('REDIS_HOST', "localhost")
PORT = os.getenv('REDIS_PORT', 6379)
PW = os.getenv('REDIS_PASSWORD', None)
SCRT = os.getenv('SECRET_JWT', "idk")

red = redis.Redis(host=HOST, port=PORT, password=PW, decode_responses=True)


def check_token(token: str) -> dict | None:
    try:
        data = jwt.decode(token, SCRT, algorithms=["HS256"])
        id = data.get("id", -1)
        value = red.get(f"jwt:{id}")
        if value == token and value is not None:
            return data
    except Exception as e:
        print(e)
    return None
