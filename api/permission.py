import asyncio
from db import db, users
from api import _ext as ext

__all__ = ["create", "override", "check"]

def create(name: str, display_name: str, toggleable: bool = True, default_enabled: bool = False) -> bool:
    """
    Register a new permission
    """
    extension = ext()
    if ":" not in name:
        name = f"{extension}:{name}"

    exists = db.single(f"SELECT * FROM {db.SCHEMA.as_string()}.perm where name = %s", (name,))
    if not exists:
        db.insert("perm", ("name",), ("display_name", "toggleable", "default_enabled", "source"), (name, display_name, toggleable, default_enabled, extension))
        return True
    return False

def check(server_id: int, user_id: int, permission: str) -> bool:
    """
    User permission check.
    This function must be called using await.
    """
    # i hate async i hate async i hate async
    if permission is None:
        future = asyncio.get_running_loop().create_future()
        future.set_result(True)
        return future
    if ":" not in permission:
        extension = ext()
        permission = f"{extension}:{permission}"
    return asyncio.create_task(users.check_permission(server_id, user_id, permission))
