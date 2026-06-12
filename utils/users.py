"""
Interact with user profiles at a lower level than the api
"""
import discord, os
from modules.bot import bot
from utils import config, jsonIO
from pathlib import Path
DIR = Path(__file__).resolve().parent.parent
__all__ = [
    "get_user_profile", "permissions", "save_user_profile",
    "permission_check", "update_role"
    ]

# these are different functions because all of them need to be accessed at some point
def get_user_profile(user_id: int) -> dict:
    filepath = f"{DIR}/data/users/{user_id}.json"
    if Path(filepath).exists():
        uesr = jsonIO.load(filepath)
        return user
    else:
        user = jsonIO.load(f"{DIR}/data/static/user.json")
        user["id"] = user_id
        dc_user: discord.Member = bot.guilds[0].get_member(user_id)
        user["roles"] = [role.id for role in dc_user.roles]
        return permissions(user)
    
def permissions(user: dict):
    for k in config.permissions_config:
        if k in user["permissions"]:
            continue
        user["permissions"][k] = None # config.permissions_config[k]["default_enabled"]
    return save_user_profile(user)

def save_user_profile(user: dict) -> dict:
    filepath = f"{DIR}/data/users/{user["id"]}.json"
    jsonIO.dump(filepath, user)
    return user

ternary = bool | None
async def permission_check(user_id: int, permission: str) -> bool:
    # Bot admin bypass check
    if user_id in config.server_config["bot_admins"]:
        return True
    
    # Ensure permission exists
    if permission not in config.permissions_config:
        raise KeyError("Permission not found.")
    
    # local user layer
    user_profile = get_user_profile(user_id)
    try:
        profile_permission = user_profile["permissions"][permission]
    except:
        user_profile = permissions(user_profile)
        profile_permission = user_profile["permissions"][permission]
    if profile_permission is not None:
        return profile_permission
    
    # safety
    if "roles" not in user_profile:
        user_profile["roles"] = [role.id for role in bot.guilds[0].get_member(user_id).roles]
        save_user_profile(user_profile)
    
    # role layer
    for role in reversed(user_profile["roles"]):
        filepath = f"{DIR}/data/roles/{role}"
        if not os.path.exists(filepath):
            continue
        role = jsonIO.load(filepath)
        if permission not in role:
            role = update_role()
        if role[permission] is not None:
            return role[permission]
    
    # default layer
    return config.permissions_config[permission]["default_enabled"]
            
def update_role(role_id):
    filepath = f"{DIR}/data/roles/{role_id}.json"
    if os.path.exists(filepath):
        role = jsonIO.load(filepath)
    else:
        role = {}
    for name, permission in config.permissions_config.items():
        if not permission["role_assignable"]:
            continue
        if name not in role:
            role[name] = None # permission["default_enabled"]
    jsonIO.dump(filepath, role)
    return role