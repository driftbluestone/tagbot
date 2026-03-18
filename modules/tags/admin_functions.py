from discord.ext import commands
from pathlib import Path
from modules.config import server_config, save_server_config
from modules.tags.users import resolve_user, get_user_profile, save_user_profile

async def admin_promote(ctx: commands.Context, message: str):
    "Gives a user the tag_admin permission"
    user = message[0]
    if user == "": return await ctx.reply(":information_source: %t admin promote `user`")
    user = await resolve_user(ctx, user)
    if not user: return await ctx.reply(":warning: Couldn't find user.")
    msg = ":white_check_mark: Sucessfully "
    if user["permissions"]["tag_admin"]:
        msg += "demoted"
        user["permissions"]["tag_admin"] = False
    else:
        msg += "promoted"
        user["permissions"]["tag_admin"] = True
    save_user_profile(user)
    return await ctx.reply(f"{msg} <@{user["id"]}>.")

async def admin_limit(ctx, _):
    "Limit tag creation to admins"
    msg = ":white_check_mark: "
    if server_config["limit_tags_to_admins"]:
        msg += "Only admins"
        server_config["limit_tags_to_admins"] = False
    else:
        msg += "Any user"
        server_config["limit_tags_to_admins"] = True
    await save_server_config()
    return await ctx.reply(f"{msg} can now create tags.")

async def admin_ban(ctx, message):
    "Ban users from creating tags, viewing tags, and using sed"
    user = message[0]
    type = message[1]
    if (user == "") or (type == "") or (type not in ["add", "view", "sed"]): return await ctx.reply(":information_source: %t admin ban `user` `add|view|sed`")
    user = await resolve_user(ctx, user)
    if not user: return await ctx.reply(":warning: Couldn't find user.")
    user = get_user_profile(user["id"])
    if type == "add":
        type = "create_tags"
    elif type == "view":
        type = "view_tags"
    elif type == "sed":
        type = "use_sed"
    ban = ""
    if user["permissions"][type]:
        user["permissions"][type] = False
    else:
        ban = "un"
        user["permissions"][type] = True
    save_user_profile(user)
    return await ctx.reply(f":white_check_mark: <@{user["id"]}> {ban}banned.")