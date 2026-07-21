"""
Interact with user profiles at a lower level than the api
"""
from typing import Any
from psycopg import sql
from utils.bot import bot
from utils import config
from utils import db, jsonIO

def get_user_profile(user_id: int) -> dict:
    """
    deprecated, use get_user instead
    """
    perms = db.get("user_perms", (bot.guilds[0].id, user_id), ("server_id", "user_id"), ("perms",),)
    data = db.get("user_data", (user_id,), ("user_id"), ("data",))
    if perms is None:
        perms = {}
    if data is None:
        data = get_user_data(user_id)
    user = {"id": user_id, "permissions": perms}
    user.update(data)
    return user

def get_user(server_id: int, user_id: int) -> tuple[dict[str, bool | None], dict[str, Any]]:
    perms = db.get("user_perms", (server_id, user_id), ("server_id", "user_id"), ("perms",),)
    data = db.get("user_data", (user_id,), ("user_id",), ("data",))
    if perms is None:
        perms = {}
    if data is not None:
        return perms, data
    db.insert("user_data", ("user_id", "data") (user_id, jsonIO.dumps(config.user_config)))
    return get_user(server_id, user_id)

def get_user_permissions(server_id, user_id: int) -> dict:
    perms = db.get("user_perms", (server_id, user_id), ("server_id", "user_id"), ("perms",))
    if perms is None:
        return {}
    return perms

def get_user_data(user_id: int) -> dict:
    data = db.get("user_data", (user_id,), ("user_id",), ("data",))
    if data is None:
        db.insert("user_data", ("user_id", "data") (user_id, jsonIO.dumps(config.user_config)))
    return get_user_data(user_id)

def permissions(user: tuple):
    if isinstance(user, tuple):
        perms = {}
        for k in config.permissions_config:
            if k in user: continue
            perms[k] = None
        user[0].update(perms)
    else:
        for k in config.permissions_config:
            if k in user["permissions"]: continue
            user["permissions"][k] = None
    return save_user_profile(user)

def save_user_profile(user: dict):
    """
    Depricated, user save_user() instead.
    """
    server_id = bot.guilds[0].id
    usr = user.copy()
    usr.pop("id")
    usr.pop("permissions")
    save_user(server_id, user["id"], (user["permissions"], usr))

def save_user(server_id: int, user_id: int, user: tuple[dict, dict]):
    """
    Save both user permissions and user data. `user` must be a tuple of the perms dict and the user data dict
    """
    perms, data = user
    save_user_permissions(server_id, user_id, perms)
    save_user_data(user_id, data)

def save_user_permissions(server_id: int, user_id: int, permissions: dict):
    db.insert("user_perms", ("server_id", "user_id",), ("perms",), (server_id, user_id, jsonIO.dumps(permissions)))

def save_user_data(user_id: int, data: dict):
    db.insert("user_data", ("user_id",) ("data",), (user_id, jsonIO.dumps(data)))

async def check_permission(server_id: int, user_id: int, permission: str) -> bool:
    # Bot admin bypass check
    if user_id in config.server_config["bot_admins"]:
        return True

    # Ensure permission exists
    if permission not in config.permissions_config:
        raise KeyError(f"Permission not found: {permission}")

async def permission_check(user_id: int, permission: str) -> bool:
    # Bot admin bypass check
    if user_id in config.server_config["bot_admins"]:
        return True

    # Ensure permission exists
    if permission not in config.permissions_config:
        raise KeyError(f"Permission not found: {permission}")
    


    ### everything below this is depricated
    # local user layer
    perms = get_user_permissions(user_id)
    if permission not in perms:
        pass
        perms = permissions(get_user(user_id))[1]
    profile_permission = perms[permission]
    
    if profile_permission is not None:
        return profile_permission

    # role layer
    for role in reversed(bot.guilds[0].get_member(user_id).roles):
        _role = db.get("role", role.id, "perms")
        if _role is None:
            continue
        if permission not in _role:
            _role = update_role(role.id)
        if _role[permission] is not None:
            return _role[permission]

    # default layer
    return config.permissions_config[permission]["default_enabled"]

def update_role(role_id):
    role, = db.get("role", role_id, "perms")
    if role is None:
        role = {}
    for name, permission in config.permissions_config.items():
        if not permission["role_assignable"]:
            continue
        if name not in role:
            role[name] = None
    db.insert("role", ("id", "perms"), (role_id, jsonIO.dumps(role)))
    return role
