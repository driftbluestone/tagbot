import subprocess, discord, json
from uuid import uuid4
from discord.ext import commands
from pathlib import Path
from modules.message_modules.message_embed import create_message_embed
from modules.tags import users, functions, admin_functions
from modules.tags.tag_utils import get_tag_data
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

async def get_tag(ctx: commands.Context, tag: str, message: list):
    if not await users.permission_check(ctx.author, "view_tags"): return await ctx.reply(":warning: You have been banned from viewing tags.")
    if not tag:
        return await ctx.reply(f":information_source: %t `{"|".join(DISPLAYED_SPECIAL_TAGS)}`")
    tag.lower()
    if tag in SPECIAL_TAGS:
        if not message: message = ["", ""]
        message[0].lower
        action =  getattr(functions, f"tag_{tag}")
        return await action(ctx, message)
    elif tag == "admin":
        return await admin_tag(ctx, message[0].lower, message[1:])
    
    user_id = str(ctx.author.id)
    data, filepath, exists, _ = await get_tag_data(user_id, tag)
    if not exists:
        search = await functions.tag_search(ctx, [tag, 1])
        return await ctx.reply(f":warning: Tag **{tag}** not found, did you mean {search}?")
    await parse_tag(ctx, data, filepath)
    
async def admin_tag(ctx: commands.Context, tag: str, message: list):
    if not await users.permission_check(ctx.author, "tag_admin"): return await ctx.reply(":warning: No permission.")
    if not message: message = ["", ""]
    tag.lower()
    if (not tag) or ( tag not in ADMIN_TAGS):
        return await ctx.reply(f":information_source: %t `{"|".join(DISPLAYED_ADMIN_TAGS)}`")
    if action in ADMIN_TAGS and action in SPECIAL_TAGS:
        action =  getattr(functions, f"tag_{tag}")
        return await action(ctx, message, True)
    action = getattr(admin_functions, f"admin_{tag}")
    return await action(ctx, message, True)

async def execute_tag(ctx: commands.Context, tag: str):
    "Executes tags while ignoring special tags"
    user_id = str(ctx.author.id)
    data, filepath, exists, _ = await get_tag_data(user_id, tag)
    if not exists: return await ctx.reply(f":warning: Tag **{tag}** not found")
    return await parse_tag(ctx, data, filepath)

async def parse_tag(ctx: commands.Context, data: dict, filepath: str, message = ""):
    "From tag data and filepath, will determine how to parse the tag"
    name = data["name"]
    tag = data["type"]
    if tag == "code":
        return await container(ctx, name, message)
    elif tag == "alias":
        return await execute_tag(ctx, tag)
    elif tag == "message":
        embed = await create_message_embed(data["link"], ctx.bot)
        return await ctx.reply(embed=embed)
    with open(f"{filepath[:-5]}.txt") as file:
        input = file.read()
    print(input)
    embed, text = await json_parser(ctx, input)
    if not embed and not text: return
    return await ctx.reply(content=text, embed=embed)

async def json_parser(ctx: commands.Context, input: str):
    "Returns an embed, calls a tag, or returns plaintext. data is returned as discord.Embed, text"
    text = None
    try:
        input = json.loads(input)
        if "call_tag" in input:
            await execute_tag(ctx, input["call_tag"])
            return None, None
        elif "embed" in input:
            embed = await embed_builder(ctx, input["embed"])
        if not isinstance(embed, discord.Embed):
            embed = discord.Embed(description=f"Error creating embed:\n{embed}")
    except json.JSONDecodeError:
        embed = None
        text = input
    
    return embed, text

async def embed_builder(ctx: commands.Context, input: dict):
    "Creates an embed from a dictionary input"
    try:
        embed = discord.Embed(**input)
    except Exception as e:
        return str(e)
    return embed

async def container(ctx: commands.Context, tag: str, message: list):
    "Creates a docker container that will execute a code tag"
    container_name = uuid4().hex
    args = [str(ctx.author.id), ctx.author.name, str(ctx.channel.id)]
    if message is not None:
        args.extend(message)
    docargs = ['docker', 'run',
               '--name', container_name,
               '--memory', '512m',
               '--memory-swap', '512m',
               '--user', '1000:1000',
               '--pids-limit', '20',
               '--cap-drop', 'ALL',
               '--network', 'none',
               '--rm', '-v', f'{DIR}/../../data/tags/tags:/data/:ro',
               'python', 'python3', f'/data/{tag}.py',
            ]
    docargs.extend(args)
    try:
        result = subprocess.run(
            docargs,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=5
        )
        output = result.stdout

    except subprocess.TimeoutExpired as e:
        output = e.stdout if e.stdout else ""
        # Force kill the container
        subprocess.run(
            ['docker', 'rm', '-f', container_name],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        output = f"{output[1900:]}\n[PROCESS KILLED: exceeded 5s timeout]"
    except subprocess.CalledProcessError as e:
        output = e

    embed, text = await json_parser(ctx, output)
    return await ctx.reply(text=text, embed=embed)