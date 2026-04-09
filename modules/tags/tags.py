import discord, json
from discord.ext import commands
from pathlib import Path
from modules.message_modules.message_embed import create_message_embed
from modules.tags import users, functions, admin_functions, container
from modules.tags.tag_utils import get_tag_data, search
# SPECIAL_TAGS = ["add", "edit", "delete", "alias", "list", "owner", "search", "raw"]
# DISPLAYED_SPECIAL_TAGS = ["add", "edit", "delete", "alias", "list", "owner", "search"]
# ADMIN_TAGS = ["delete", "promote", "limit", "ban", "edit"]
# DISPLAYED_ADMIN_TAGS = ["delete", "promote", "limit", "ban"]
DIR = Path(__file__).resolve().parent.parent.parent
with open(f"{DIR}/data/static/special_tags.json", "r") as file:
    SPECIAL_TAGS, DISPLAYED_SPECIAL_TAGS, ADMIN_TAGS, DISPLAYED_ADMIN_TAGS = json.load(file).values()

async def context_formatter(ctx: commands.Context):
    message = ctx.message.content
    message = message.split(" ")
    if len(message) != 1:
        tag = message[1]
        message = message[2:]
    else:
        tag = None
    await get_tag(ctx, tag, message)

async def get_tag(ctx: commands.Context, tag: str, message: list):
    if not await users.permission_check(ctx.author, "view_tags"): return await ctx.reply(":warning: You have been banned from viewing tags.")
    if not tag:
        return await ctx.reply(f":information_source: %t `{"|".join(DISPLAYED_SPECIAL_TAGS)}`")
    tag.lower()
    if tag in SPECIAL_TAGS:
        if not message: message = ["", ""]
        message[0].lower()
        action =  getattr(functions, f"tag_{tag}")
        return await action(ctx, message)
    elif tag == "admin":
        if not message: message = ["", ""]
        return await admin_tag(ctx, message[0].lower(), message[1:])
    
    user_id = str(ctx.author.id)
    data, filepath, exists, _ = await get_tag_data(user_id, tag)
    if not exists:
        match = await search(tag, 1)
        return await ctx.reply(f":warning: Tag **{tag}** not found, did you mean {match}?")
    await parse_tag(ctx, data, filepath, message)
    
async def admin_tag(ctx: commands.Context, tag: str, message: list):
    if not await users.permission_check(ctx.author, "tag_admin"): return await ctx.reply(":warning: No permission.")
    if not message: message = ["", ""]
    tag.lower()
    if (not tag) or (tag not in ADMIN_TAGS):
        return await ctx.reply(f":information_source: %t `{"|".join(DISPLAYED_ADMIN_TAGS)}`")
    if tag in ADMIN_TAGS and tag in SPECIAL_TAGS:
        action =  getattr(functions, f"tag_{tag}")
        return await action(ctx, message, True)
    action = getattr(admin_functions, f"admin_{tag}")
    return await action(ctx, message, True)

async def execute_tag(ctx: commands.Context, tag: str, message: list = []):
    """Executes tags while ignoring special tags"""
    user_id = str(ctx.author.id)
    data, filepath, exists, _ = await get_tag_data(user_id, tag)
    if not exists: return await ctx.reply(f":warning: Tag **{tag}** not found")
    return await parse_tag(ctx, data, filepath, message)

async def parse_tag(ctx: commands.Context, data: dict, filepath: str, message: list = []):
    """From tag data and filepath, will determine how to parse the tag"""

    # Set a recursion limit for code tag calling
    setattr(ctx, "recursion", getattr(ctx, "recursion", 0)+1)
    if ctx.recursion >= 5:
        return await ctx.reply(":warning: Tag recursion limit reached.")
    
    name = data["name"]
    tag = data["type"]
    if tag == "code":
        return await container(ctx, name, message)
    elif tag == "alias":
        return await execute_tag(ctx, data["alias_of"])
    elif tag == "message":
        embed = await create_message_embed(data["message_link"], ctx.bot)
        return await ctx.reply(embed=embed)
    with open(f"{filepath[:-5]}.txt") as file:
        input = file.read()
    embed, text = await json_parser(ctx, input)
    if not embed and not text: return
    return await ctx.reply(content=text, embed=embed)

async def json_parser(ctx: commands.Context, input: str):
    """Returns an embed, calls a tag, or returns plaintext. data is returned as discord.Embed, text"""
    text = None
    try:
        json_input = json.loads(input)
        if not isinstance(json_input, dict):
            return None, input
        if "call_tag" in json_input:
            if "args" in json_input: await execute_tag(ctx, json_input["call_tag"], json_input["args"])
            else: await execute_tag(ctx, json_input["call_tag"])
            return None, None
        elif "embed" in json_input:
            embed = await embed_builder(ctx, input["embed"])
        else:
            return None, input
        if not isinstance(embed, discord.Embed):
            embed = discord.Embed(description=f"Error creating embed:\n{embed}")

    except json.JSONDecodeError:
        embed = None
        text = input[:1995]
    return embed, text

async def embed_builder(ctx: commands.Context, input: dict):
    "Creates an embed from a dictionary input"
    embed = discord.Embed()
    for k, v in input.items():
        try:
            if isinstance(v, dict): getattr(embed, k)(**v)
            else: setattr(embed, k, v) 
        except Exception as e:
            return str(e)
        
    return embed

async def execute_code_tag(ctx: commands.Context, tag: str, message: list):
    output = await container.container(ctx, tag, message)
    embed, text = await json_parser(ctx, output)
    if embed is None and text is None: return
    return await ctx.reply(content=text, embed=embed)
