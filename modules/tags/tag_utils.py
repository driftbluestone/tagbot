import pathlib, json
from modules import config
from modules.tags import users
DIR = pathlib.Path(__file__).resolve().parent

async def get_tag_data(ctx, tag, require_exists, require_owned):
    filepath =f"{DIR}/../../data/tags/tags/{tag}.json"
    exists = await check_tag_exists(filepath)
    if not exists and not require_exists and not require_owned:
        return True, filepath
    if not exists:
        return False, filepath
    with open(filepath, "r") as file:
        data = json.load(file)
    if exists == require_exists and not require_owned:
        return data, filepath
    owner = await check_tag_owner(data, str(ctx.author.id))
    if owner:
        return data, filepath
    else:
        await ctx.reply(f":warning: Tag **{tag}** is owned by <@{data["owner"]}>.")
        return False, filepath

async def check_creation_permission(ctx):
    limit = config.server_config["limit_tags_to_admins"]
    user = users.get_user_profile(str(ctx.author.id))
    tag_admin = user["permissions"]["tag_admin"]
    admin = ctx.author.guild_permissions.administrator
    if limit and not (tag_admin or admin):
        await ctx.reply(":information_source: Only admins can create tags")
        return False
    else:
        return True
    
async def check_tag_exists(filepath):
    if not pathlib.Path(filepath).exists():
        return False
    else: return True

async def check_tag_owner(data, id):
    if data["owner"] != id:
        return False
    else: return True