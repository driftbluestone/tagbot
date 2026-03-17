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
    ban = await users.permission_check(ctx.author, "create_tags")
    if not ban:
        await ctx.reply(":warning: You are banned from creating tags.")
        return False
    limit = config.server_config["limit_tags_to_admins"]
    admin = await users.permission_check(ctx.author, "tag_admin")
    if limit and (not admin):
        await ctx.reply(":information_source: Only admins can add tags")
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
