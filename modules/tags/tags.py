from pathlib import Path
from modules.tags import users, functions
DIR = Path(__file__).resolve().parent.parent.parent

SPECIAL_TAGS = ["add", "edit", "delete", "alias", "list", "owner", "search", "raw"]
DISPLAYED_SPECIAL_TAGS = ["add", "edit", "delete", "alias", "list", "owner", "search"]
ADMIN_TAGS = ["delete", "promote", "limit", "ban"]


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
    if tag == None:
        return await ctx.reply(f":information_source: %t `{"|".join(DISPLAYED_SPECIAL_TAGS)}`")
    tag.lower()
    if tag in SPECIAL_TAGS:
        if message == []:
            message = ["", ""]
        message[0].lower
        action =  getattr(functions, f"tag_{tag}")
        return await action(ctx, message)
    if tag == "admin":
        pass

# elif tag == "raw":
#     await raw_tag(ctx, message[0])
# elif tag == "admin":
#     await admin_tag(ctx, message[0], message[1:])