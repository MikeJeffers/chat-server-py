import psycopg2
import os
from dotenv import load_dotenv
import logging

load_dotenv()

DB_HOST = os.getenv('POSTGRES_HOST', "localhost")
DB_NAME = os.getenv('POSTGRES_DB', "test")
DB_USER = os.getenv('POSTGRES_USER', "user")
DB_PASS = os.getenv('POSTGRES_PASSWORD', "password")


def db():
    return psycopg2.connect(dbname=DB_NAME, password=DB_PASS, user=DB_USER, host=DB_HOST)


def get_user(id: int, psql):
    with psql.cursor() as cur:
        try:
            cur.execute("SELECT id, username FROM Users WHERE id=%s LIMIT 1",
                        (id,))
            data = cur.fetchone()
            if not data or len(data)!=2:
                raise Exception("bad data")
            id, username = data
            return {"username": username, "id": id}
        except Exception as e:
            logging.warning("Failed to lookup user with id %d" % id)
            return None
