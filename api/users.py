import json, discord
from api import _ext as ext
from pathlib import Path
from utils import users, config
from modules.bot import bot
DIR = Path(__file__).resolve().parent.parent

def new_data_field(name: str | list[str], data_type: type | list[type]) -> bool:
    """
    Define a new field for storing data in user json files.
    data_type must be a json compatible type.

    To register multiple data fields at once, both name and data_type must be lists, and must be equal in length.

    If any data fields are already in the user config file, the registration will fail and the function will return False.
    """
    extension = ext()
    
    def _register(name: str, data_type: type) -> bool:
        id = f"{extension}:{name}"
        if id not in config.user_config:
            config.user_config[id] = data_type()
            return True
        return False
    
    if isinstance(name, list):
        for nm, dt in zip(name, data_type, strict=True):
            if not _register(nm, dt): return False
    else:
        if not _register(name, data_type): return False
    config.save_user_config()
    return True

async def has_permission(user_id: int, permission: str) -> bool:
    """
    User permission check
    """
    return await users.permission_check(user_id, permission)

def get(user_id: int) -> dict:
    """
    Get sonny user profile
    """
    return users.get_user_profile(user_id)

def set_field(user_id: int, field, data):
    """
    Set user data and automatically save it to disk.
    Will raise a KeyError if the field is not in the user profile
    """
    user = users.get_user_profile(user_id)
    if field not in user:
        raise KeyError
    user[field] = data
    with open(f"{DIR}/data/users/{user_id}.json", "w") as file:
        json.dump(user, file, indent=2)

def toggle_permission(user_id: int, permission) -> bool:
    """
    Toggle user permission. Returns the updated value.
    """
    user = users.get_user_profile(user_id)
    user["permissions"][permission] = not user["permissions"][permission]
    with open(f"{DIR}/data/users/{user_id}.json", "w") as file:
        json.dump(user, file)
    return user["permissions"][permission]

async def resolve_user(user: str | int) -> tuple[dict, discord.User] | False:
    if user.startswith("<@") and user.endswith(">"):
        user = user[2:-1]
        user_object = await bot.guilds[0].get_member(user)
    else:
        user_object = bot.guilds[0].get_member_named(user)
    if user_object == None:
        try:
            user = int(user)    
            user_object = bot.guilds[0].get_member(user)
        except:
            return False
    if user_object == None:
            return False
    return users.get_user_profile(user_object.id), user_object