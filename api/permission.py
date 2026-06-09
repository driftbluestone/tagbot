from pathlib import Path
from utils import users, config
from api import _ext as ext
DIR = Path(__file__).resolve().parent.parent

def create(name: str, display_name: str, toggleable: bool = True, default_enabled: bool = False, role_assignable: bool = True) -> bool:
    """
    Register a new permission, setting discord_equivalent to None will also make the permission enabled by default
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
    User permission check, permission must be formatted as `namespace:permission`
    """
    return await users.permission_check(user_id, permission)