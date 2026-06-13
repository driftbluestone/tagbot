import discord, os, asyncio
from utils.bot import bot
from utils import users, config, jsonIO
from api import _ext as ext
from utils.utils import DIR

def new_data_field(name: str, data_type: type) -> bool:
    """
    Define a new field for storing data in user json files.
    data_type must be a json compatible type.

    If any data fields are already in the user config file, the registration will fail and the function will return False.
    """
    if ":" not in name:
        extension = ext()
    else:
        extension, name = name.split(":")

    def _register(id: str, data_type: type) -> bool:
        if id not in config.user_config:
            config.user_config[id] = data_type()
            return True
        return False

    id = f"{extension}:{name}"
    if not _register(id, data_type):
        return False

    config.save_user_config()

    # update existing user files

    for user_file in os.listdir(f"{DIR}/data/users"):
        user = jsonIO.load(f"{DIR}/data/users/{user_file}")
        user[id] = data_type()
        jsonIO.dump(f"{DIR}/data/users/{user_file}", user)

    return True

def has_permission(user_id: int, permission: str) -> bool:
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
    jsonIO.dump(f"{DIR}/data/users/{user_id}.json", user)

def overwrite(user: dict) -> dict:
    """
    Overwrite all data for this user
    """
    return users.save_user_profile(user)

def toggle_permission(user_id: int, permission) -> bool:
    """
    Toggle user permission. Returns the updated value.
    """
    user = users.get_user_profile(user_id)
    user["permissions"][permission] = not user["permissions"][permission]
    jsonIO.dump(f"{DIR}/data/users/{user_id}.json", user)
    return user["permissions"][permission]

async def resolve_user(user: str | int) -> tuple[dict, discord.Member] | False:
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
