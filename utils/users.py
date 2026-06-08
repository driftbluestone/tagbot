import discord, json, os
from utils import config
from modules.bot import bot
from pathlib import Path
DIR = Path(__file__).resolve().parent.parent

# these are different functions because all of them need to be accessed at some point
def get_user_profile(user_id: int) -> dict:
    filepath = f"{DIR}/data/users/{user_id}.json"
    if Path(filepath).exists():
        with open(filepath, "r") as file:
            user = json.load(file)
        return user
    else:
        with open(f"{DIR}/data/static/user.json", "r") as file:
            user = json.load(file)  
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
    with open(filepath, "w") as file:
        json.dump(user, file, indent=2)
    return user

ternary = bool | None
async def permission_check(user_id: int, permission: str) -> bool:
    if permission is None:
        return True
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
    
    # role layer
    user: discord.Member = bot.guilds[0].get_member(user_id)
    roles = list(reversed(user.roles)) 
    for role in roles:
        filepath = f"{DIR}/data/roles/{role.id}"
        if not os.path.exists(filepath):
            continue
        with open(filepath, "r") as file:
            role = json.load(file)
        if permission not in role:
            role = update_role()
        if role[permission] is not None:
            return role[permission]
    
    # default layer
    return config.permissions_config[permission]["default_enabled"]
            
def update_role(role_id):
    filepath = f"{DIR}/data/roles/{role_id}.json"
    if os.path.exists(filepath):
        with open(filepath, "r") as file:
            role = json.load(file)
    else:
        role = {}
    for name, permission in config.permissions_config.items():
        if not permission["role_assignable"]:
            continue
        if name not in role:
            role[name] = None # permission["default_enabled"]
    with open(filepath, "w") as file:
        json.dump(role, file, indent=2)
    return role