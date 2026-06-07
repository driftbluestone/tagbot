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
        return permissions(user)
    
def permissions(user):
    for k in config.permissions_config:
        if k in user["permissions"]:
            continue
        user["permissions"][k] = None # config.permissions_config[k]["default_enabled"]
    return save_user_profile(user)

def save_user_profile(user):
    filepath = f"{DIR}/data/users/{user["id"]}.json"
    with open(filepath, "w") as file:
        json.dump(user, file, indent=2)
    return user

async def permission_check(user_id: int, permission: str) -> bool:
    if permission is None:
        return True
    if user_id in config.server_config["bot_admins"]:
        return True
    user_profile = get_user_profile(user_id)
    if permission not in config.permissions_config:
        raise KeyError("Permission not found.")
    
    if config.permissions_config[permission]["discord_equivalent"] != None:
        user: discord.Member = bot.guilds[0].get_member(user_id)
        discord_permissions = getattr(user.guild_permissions, config.permissions_config[permission]["discord_equivalent"], False)
        if discord_permissions:
            return discord_permissions
        
    try:
        profile_permission = user_profile["permissions"][permission]
    except:
        user_profile = permissions(user_profile)
        profile_permission = user_profile["permissions"][permission]
    if profile_permission:
        return True
    
    for role in user.roles:
        filepath = f"{DIR}/data/roles/{role.id}"
        if not os.path.exists(filepath):
            continue
        with open(filepath, "r") as file:
            role = json.load(file)
        if permission not in role:
            role = update_role()
        if role[permission]:
            return True
    return False
            
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