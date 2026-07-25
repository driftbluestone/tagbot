from typing import Literal, Any
from db import db

def get_server(server_id: int, fields: tuple[Literal["perms", "extensions", "default_user_data","command_prefix", "*"], ...]):
    return db.get("server", (server_id,), ("server_id",), fields)

def update_server(server_id: int, fields: tuple[Literal["perms", "extensions", "default_user_data","command_prefix", "*"], ...], value: tuple[Any]):
    db.insert("server", ("server_id"), fields, (server_id,) + value)