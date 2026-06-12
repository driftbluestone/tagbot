import asyncio
from utils import users, config
from api import _ext as ext
from pathlib import Path
from utils.utils import DIR

def create(name: str, display_name: str, toggleable: bool = True, default_enabled: bool = False, role_assignable: bool = True) -> bool:
    """
    Register a new permission
    """
    extension = ext()

    id = f"{extension}:{name}"
    config.permissions_config[id] = {
        "display_name": display_name,
        "toggleable": toggleable,
        "default_enabled": default_enabled,
        "role_assignable": role_assignable
    }
    config.save_permisions_config()
    return True

def override(namespace: str, permission: str, new_equiv: str) -> bool:
    """
    Returns True on success, returns False on failure to override, usually because the extension is not installed or does not have that permission
    """
    namespaces, perms = zip(*[x.split(":") for x in config.permissions_config.keys()])
    if namespace in namespaces and permission in perms:
        config.permissions_config[f"{namespace}:{permission}"]["discord_equivalent"] = new_equiv
        config.save_permisions_config()
        return True
    return False

async def check(user_id: int, permission: str) -> bool:
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
    return asyncio.create_task(users.permission_check(user_id, permission))
