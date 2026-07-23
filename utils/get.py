from typing import Any, Literal
from utils import db, jsonIO

def server(server_id: int, fields: tuple[Literal["perms", "extensions", "default_user_data","command_prefix", "*"], ...]):
    if isinstance(fields, str):
        fields = (fields,)
    return db.get("server", (server_id,), ("server_id",), fields)

def user(server_id: int, user_id: int) -> tuple[dict[str, bool | None], dict[str, Any]]:
    """
    Retrieve both user permissions and data, recommended to use their specific functions if you only need one of the two.
    """
    perms = db.get("user_perms", (server_id, user_id), ("server_id", "user_id"), ("perms",),)
    data = db.get("user_data", (user_id,), ("user_id",), ("data",))
    if perms is None:
        perms = {}
    if data is not None:
        return perms, data
    db.insert("user_data", ("user_id", "data") (user_id, jsonIO.dumps(server(server_id, "default_user_data"))))
    return user(server_id, user_id)

def user_permissions(server_id, user_id: int) -> dict:
    perms = db.get("user_perms", (server_id, user_id), ("server_id", "user_id"), ("perms",))
    if perms is None:
        return {}
    return perms

def user_server_data(server_id, user_id: int) -> dict:
    data = db.get("user_data", (user_id,), ("user_id",), ("data",))
    if data is None:
        db.insert("user_data", ("user_id", "data") (user_id, jsonIO.dumps(server(server_id, "default_user_data"))))
    return user_server_data(user_id)