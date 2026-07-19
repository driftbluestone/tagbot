import asyncio
from utils import users, config
from api import _ext as ext

__all__ = ["create", "override", "check"]

def create(name: str, display_name: str, toggleable: bool = True, default_enabled: bool = False, role_assignable: bool = True) -> bool:
    """
    Register a new permission
    """
    if "." in name:
        raise ValueError("Permission names cannot contain '.'")
    
    if ":" in name:
        extension, name = name.split(":")
    else:
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

def check(user_id: int, permission: str) -> bool:
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

def group(name: str):
    """
    Register a new permission group. Permissions within groups are saved as `namespace.group:permission`.
    """
    if ":" in name:
        extension, name = name.split(":")
    elif "." in name:
        extension, name = name.split(":")
    else:
        extension = ext()
    id = f"{extension}.{name}"
    if id not in config.permissions_config():
        config.permissions_config[id] = {}
        config.save_permisions_config()
        return True
    return False

class Group: 
    def __init__(self, name: str):
        if ":" in name:
            self.ext, self.name = name.split(":")
        elif "." in name:
            self.ext, self.name = name.split(".")
        else:
            self.name = name
            self.ext = ext()
        self.group = f"{self.ext}.{self.name}"
    
    def check(self, user_id: int, permission: str) -> bool:
        return check(user_id, f"{self.ext}.{self.name}:{permission}")
    
    def create(self, name: str, display_name: str, toggleable: bool = True, default_enabled: bool = False, role_assignable: bool = True):
        if name in config.permissions_config[self.group]:
            return False
        config.permissions_config[self.group][name] = {
            "display_name": display_name,
            "toggleable": toggleable,
            "default_enabled": default_enabled,
            "role_assignable": role_assignable
        }
        config.save_permisions_config()
        return True
    