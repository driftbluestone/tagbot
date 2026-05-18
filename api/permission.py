import json
from pathlib import Path
from utils import users, config
from api import _ext as ext
DIR = Path(__file__).resolve().parent.parent

def create(name: str | list, discord_equivalent: None|str | list[None|str]) -> bool:
    """
    Register a new permission, setting discord_equivalent to None will also make the permission enabled by default
    """
    extension = ext()
    
    if isinstance(name, list):
        for nm, eq in zip(name, discord_equivalent, strict=True):
            id = f"{extension}:{nm}"
            config.permissions_config[id] = eq
    else:
        id = f"{extension}:{nm}"
        config.permissions_config[id] = discord_equivalent
    config.save_permisions_config()
    return True

def override(namespace: str, permission: str, new_equiv: str) -> bool:
    """
    Returns True on success, returns False on failure to override, usually because the extension is not installed or does not have that permission
    """
    namespaces, perms = zip(*[x.split(":") for x in config.permissions_config.keys()])
    if namespace in namespaces and permission in perms:
        config.permissions_config[f"{namespace}:{permission}"] = new_equiv
        config.save_permisions_config()
        return True
    return False

async def check(user_id: int, permission: str) -> bool:
    """
    User permission check
    """
    if ":" not in permission:
        extension = ext()
        permission = f"{extension}:{permission}"
    return await users.permission_check(user_id, permission)