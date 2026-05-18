import discord, json
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
    for k in config.permissions_config.keys():
        if k in user["permissions"].keys():
            continue
        if config.permissions_config[k] == None:
            user["permissions"][k] = True
            continue
        user["permissions"][k] = False
    return save_user_profile(user)
def save_user_profile(user):
    filepath = f"{DIR}/data/users/{user["id"]}.json"
    with open(filepath, "w") as file:
        json.dump(user, file, indent=2)
    return user

async def permission_check(user_id: int, permission: str):
    if permission is None:
        return True
    if user_id in config.server_config["bot_admins"]:
        return True
    user_profile = get_user_profile(user_id)
    if permission not in config.permissions_config:
        raise KeyError("Permission not found.")
    if config.permissions_config[permission] != None:
        user: discord.Member = bot.guilds[0].get_member(user_id)
        discord_permissions = getattr(user.guild_permissions, config.permissions_config[permission], False)
        if discord_permissions:
            return discord_permissions
    try:
        profile_permission = user_profile["permissions"][permission]
    except:
        user_profile = permissions(user_profile)
        profile_permission = user_profile["permissions"][permission]
    
    return profile_permission
