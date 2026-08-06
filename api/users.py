import discord, asyncio
from discord.ext import commands
from psycopg import sql
from db import db, users
from utils.utils import bot
from api import _ext as ext

__all__ = ["new_data_field", "has_permission", "get", "set_field", "overwrite", "toggle_permission", "resolve_user"]

def has_permission(server_id, user_id: int, permission: str) -> bool:
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
    return asyncio.create_task(users.check_permission(server_id, user_id, permission))

def get_user_data(server_id: int, user_id: int) -> dict:
    """Get user data, for global user data, use server id 0."""
    return users.get_user_data(server_id, user_id)

def set_field(server_id: int, user_id: int, field: str, data):
    """Save user data. Use server_id 0 for global data."""
    if ":" not in field:
        extension = ext()
        field = f"{extension}:{field}"
    user_data = get_user_data(server_id, user_id)
    user_data[field] = data
    users.save_user_data(server_id, user_id, user_data)

def get_field(server_id: int, user_id: int, field: str):
    if ":" not in field:
        extension = ext()
        field = f"{extension}:{field}"
    
    query = sql.SQL("""SELECT data->>{field} FROM {schema}.user
        WHERE server_id = {server_id} AND user_id = {user_id};""").format(
            schema = db.SCHEMA,
            field = sql.Literal(field),
            server_id = sql.Placeholder(),
            user_id = sql.Placeholder()
        )
    result, = db.single(query, (server_id, user_id))
    return result

def overwrite(server_id: int, user_id: int, user: dict):
    """Overwrite all data for this user"""
    users.save_user_data(server_id, user_id, user)

async def resolve_user(server_id: int, user: str | int) -> tuple[dict, discord.Member] | tuple[False, False]:
    if user.startswith("<@") and user.endswith(">"):
        user = user[2:-1]
    user_object = bot.get_guild(server_id).get_member_named(user.lower())
    if user_object == None:
        try:
            user = int(user)
            user_object = bot.get_guild(server_id).get_member(user)
        except:
            return False, False
    if user_object == None:
            return False, False
    return users.get_user_data(server_id, user_object.id), user_object
