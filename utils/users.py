"""
Interact with user profiles at a lower level than the api
"""
from utils.bot import bot
from utils import config
from utils import db, jsonIO
from utils.utils import DIR

# these are different functions because all of them need to be accessed at some point
def get_user_profile(user_id: int) -> dict:
    "deprecated"
    user = db.get("user", user_id)
    print(user)
    if user is not None:
        id, perms, data = user
        user = {"id": id, "permissions": perms}
        user.update(data)
        return user
    
    return permissions((user_id, {}, config.user_config))

def get_user(user_id: int) -> tuple:
    user = db.get("user", user_id)
    if user is not None:
        return user
    return permissions((user_id, {}, config.user_config))

def get_user_permissions(user_id: int) -> dict:
    perms = db.get("user", user_id, "perms")
    
    if perms is None:
        user = get_user(user_id)
        perms = user[1]
    return perms

def permissions(user: tuple):
    if isinstance(user, tuple):
        perms = {}
        for k in config.permissions_config:
            if k in user: continue
            perms[k] = None
        user[1].update(perms)
    else:
        for k in config.permissions_config:
            if k in user["permissions"]: continue
            user["permissions"][k] = None
    return save_user_profile(user)

def save_user_profile(user: tuple) -> tuple:
    if isinstance(user, dict):
        usr = user.copy()
        usr.pop("id")
        usr.pop("permissions")
        user = (user["id"], user["permissions"], usr)
    db.insert("user", ("id", "perms", "data"), (user[0], jsonIO.dumps(user[1]), jsonIO.dumps(user[2])))
    return user

async def permission_check(user_id: int, permission: str) -> bool:
    # Bot admin bypass check
    if user_id in config.server_config["bot_admins"]:
        return True

    # Ensure permission exists
    if permission not in config.permissions_config:
        raise KeyError(f"Permission not found: {permission}")

    # local user layer
    perms = get_user_permissions(user_id)
    if permission not in perms:
        perms = get_user(user_id)[1]
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
