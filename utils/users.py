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

# im gonna cry.
async def check_permission(server_id: int, user_id: int, permission: str) -> bool:
    # Bot admin bypass check
    if user_id in config.server_config["bot_admins"]:
        return True

    # Ensure permission exists
    if permission not in config.permissions_config:
        raise KeyError(f"Permission not found: {permission}")

    # get roles
    roles = [role.id for role in reversed((bot.get_guild(server_id).get_member(user_id)).roles)]

    query = sql.SQL("""SELECT COALESCE (
            (up.perms ->> {perm})::boolean,
            (
                SELECT (perms ->> {perm})::boolean
                FROM {schema}.role r
                WHERE server_id = {server_id}
                    AND r.role_id = ANY({roles})
                    AND r.perms ->> {perm} IS NOT NULL
                ORDER BY array_position({roles}, role_id)
                ASC LIMIT 1
            ),
            (sp.perms ->> {perm})::boolean,
            ) FROM {schema}.server sp
            LEFT JOIN {schema}.role rp
            ON rp.server_id = sp.server_id
            LEFT JOIN {schema}.user_perms up
            ON up.server_id = sp.server_id
            AND up.user_id = {user_id}
            WHERE up.server_id = {server_id}
        """).format(
        schema = db.SCHEMA,
        perm = sql.Placeholder("perm"),
        server_id = sql.Placeholder("server_id"),
        user_id = sql.Placeholder("user_id"),
        roles = sql.Placeholder("roles")
    )
    result = db.single(query, {
        "perm": permission,
        "server_id": server_id,
        "user_id": user_id,
        "roles": roles
    })
    return result

async def permission_check(user_id: int, permission: str) -> bool:
    """
    depricated
    """
    return await check_permission(bot.guilds[0].id, user_id, permission)
