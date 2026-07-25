"""
Interact with user profiles at a lower level than the api
"""
from psycopg import sql
from utils.bot import bot
from utils import config, get
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
        data = get.user_data(user_id)
    user = {"id": user_id, "permissions": perms}
    user.update(data)
    return user

def save_user_profile(user: dict):
    """
    Depricated, user save_user() instead.
    """
    server_id = bot.guilds[0].id
    usr = user.copy()
    usr.pop("id")
    usr.pop("permissions")
    # save_user(server_id, user["id"], (user["permissions"], usr))

def save_permission(server_id: int, id: int, permission: str, value: bool):
    if value is None:
        return
    db.insert("permissions", ("server_id", "id", "permission"), ("value",), (server_id, id, permission, value))

def save_user_data(user_id: int, data: dict):
    db.insert("user_data", ("user_id",) ("data",), (user_id, jsonIO.dumps(data)))

# im gonna cry.
async def check_permission(server_id: int, user_id: int, permission: str) -> bool:
    # Bot admin bypass check
    if user_id in config.server_config["bot_admins"]:
        return True

    # Ensure permission exists
    if permission not in config.permissions_config:
        raise KeyError(f"Permission not found: {permission}")

    # get roles
    ids = [role.id for role in reversed((bot.get_guild(server_id).get_member(user_id)).roles)]
    ids.insert(0, user_id)
    ids.append(0)

    query = sql.SQL("""SELECT sub.value
        FROM unnest({ids})
        WITH ORDINALITY AS k(key_val, priority)
        CROSS JOIN LATERAL (
            SELECT value
            FROM {schema}.permissions
            WHERE id = k.key_val
                AND server_id = {server_id}
                AND permission = {permission}
                AND value IS NOT NULL
            LIMIT 1
        ) sub
        ORDER BY k.priority
        LIMIT 1;
        """).format(
        schema = db.SCHEMA,
        server_id = sql.Placeholder("server_id"),
        permission = sql.Placeholder("permission"),
        ids = sql.Placeholder("ids")
    )
    result = db.single(query, {
        "server_id": server_id,
        "permission": permission,
        "ids": ids
    })

    if isinstance(result, tuple):
        result = result[0]
    if result is None:
        result = False
    
    return result

async def permission_check(user_id: int, permission: str) -> bool:
    """
    depricated
    """
    return await check_permission(bot.guilds[0].id, user_id, permission)
