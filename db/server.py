from psycopg import sql
from typing import Literal, Any
from db import db

def get(server_id: int, fields: tuple[Literal["extensions", "default_user_data","command_prefix", "*"], ...] = ("*",)):
    svr, =db.get("server", (server_id,), ("server_id",), fields)
    return svr

def update(server_id: int, fields: tuple[Literal["extensions", "default_user_data","command_prefix"], ...], value: tuple[Any]):
    db.insert("server", ("server_id"), fields, (server_id,) + value)

def perms(server_id: int) -> dict[str, bool]:
    query = sql.SQL("""SELECT (permission, value)
            FROM {schema}.permissions
            WHERE server_id = {server_id}
            AND id = 0
            """).format(
        schema = db.SCHEMA,
        server_id = sql.Placeholder()
            )
    perms = db.multiple(query, server_id)

    return {k: v for k, v in perms}