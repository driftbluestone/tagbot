from psycopg import sql
from typing import Literal, Any
from db import db

def get(server_id: int, fields: tuple[Literal["command_prefix", "*"], ...] = ("*",)):
    svr, = db.get("server", (server_id,), ("server_id",), fields)
    return svr

def update(server_id: int, fields: tuple[Literal["command_prefix"], ...], value: tuple[Any]):
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

def extensions(server_id: int):
    query = sql.SQL("SELECT extension FROM {schema}.extensions WHERE server_id = {server_id}").format(
        schema = db.SCHEMA,
        server_id = sql.Placeholder()
    )
    installed = db.multiple(query, 0)
    server = db.multiple(query, server_id)
    return {k: True if k in server else False for k in installed}

def check_extension(server_id: int, extension: str):
    query = sql.SQL("SELECT * FROM {schema}.extensions WHERE server_id = {server_id} AND extension = {extension}").format(
        schema = db.SCHEMA,
        server_id = sql.Placeholder(),
        extension = sql.Placeholder
    )
    exists, = db.single(query, (server_id, extension))
    if exists is None:
        return False
    return True