import json
from pathlib import Path
from utils import users
from api import _ext as ext
DIR = Path(__file__).resolve().parent.parent

def create(name: str | list, discord_equivalent: None|str | list[None|str]) -> bool:
    """
    Register a new permission, setting discord_equivalent to None will also make the permission enabled by default
    """
    extension = ext()
    with open(f"{DIR}/data/static/permissions.json", "r") as file:
        permissions = json.load(file)
    
    def _register(name: str, eq: type) -> bool:
        id = f"{extension}:{name}"
        if id not in permissions:
            permissions[id] = eq
            return True
        return False
    
    if isinstance(name, list):
        for nm, eq in zip(name, discord_equivalent, strict=True):
            if not _register(nm, eq): return False
    else:
        if not _register(name, discord_equivalent): return False
    with open(f"{DIR}/data/static/permissions.json", "w") as file:
        json.dump(permissions, file, indent=2)

def override(namespace: str, permission: str, new_equiv: str) -> bool:
    """
    Returns True on success, returns False on failure to override, usually because the extension is not installed or does not have that permission
    """
    with open(f"{DIR}/data/static/permissions.json", "r") as file:
        permissions = json.load(file)
    namespaces, perms = zip(*[x.split(":") for x in permissions.keys()])
    if namespace in namespaces and permission in perms:
        permissions[f"{namespace}:{permission}"] = new_equiv
        with open(f"{DIR}/data/static/permissions.json", "w") as file:
            json.dump(permissions, file, indent=2)
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