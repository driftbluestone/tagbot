from pathlib import Path
from modules.tags import users, functions, admin_functions

SPECIAL_TAGS = ["add", "edit", "delete", "alias", "list", "owner", "search", "raw"]
DISPLAYED_SPECIAL_TAGS = ["add", "edit", "delete", "alias", "list", "owner", "search"]
ADMIN_TAGS = ["delete", "promote", "limit", "ban", "edit"]
DISPLAYED_ADMIN_TAGS = ["delete", "promote", "limit", "ban"]
DIR = Path(__file__).resolve().parent.parent.parent

async def context_formatter(ctx):
    message = ctx.message.content
    message = message.split(" ")
    if len(message) != 1:
        tag = message[1]
        message = message[2:]
    else:
        tag = None
    await get_tag(ctx, tag, message)

async def get_tag(ctx, tag, message):
    if not await users.permission_check(ctx.author, "view_tags"): return await ctx.reply(":warning: You have been banned from viewing tags.")
    if not tag:
        return await ctx.reply(f":information_source: %t `{"|".join(DISPLAYED_SPECIAL_TAGS)}`")
    tag.lower()
    if tag in SPECIAL_TAGS:
        if message == []: message = ["", ""]
        message[0].lower
        action =  getattr(functions, f"tag_{tag}")
        return await action(ctx, message)
    elif tag == "admin":
        return await admin_tag(ctx, message[0].lower, message[1:])

async def admin_tag(ctx, tag, message):
    if not await users.permission_check(ctx.author, "tag_admin"): return await ctx.reply(":warning: No permission.")
    if message == []: message = ["", ""]
    tag.lower()
    if (not tag) or ( tag not in ADMIN_TAGS):
        return await ctx.reply(f":information_source: %t `{"|".join(DISPLAYED_ADMIN_TAGS)}`")
    if action in ADMIN_TAGS and action in SPECIAL_TAGS:
        action =  getattr(functions, f"tag_{tag}")
        return await action(ctx, message, True)
    action = getattr(admin_functions, f"admin_{tag}")
    return await action(ctx, message, True)
