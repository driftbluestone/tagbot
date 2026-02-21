import discord, json, os, re, sys, subprocess, pathlib
from discord.ext import commands
from dataclasses import asdict
bot = commands.Bot(
    command_prefix="$",
    allowed_mentions=discord.AllowedMentions(
        users=False,
        everyone=False,
        roles=False,
        replied_user=True,
    ),
    intents=discord.Intents.all(),
)
DIR = pathlib.Path(__file__).resolve().parent

if not os.path.isdir(f"{DIR}/tags"):
    os.mkdir(f"{DIR}/tags")
if not os.path.isdir(f"{DIR}/users"):
    os.mkdir(f"{DIR}/users")

with open(f"{DIR}/TOKEN.txt", "r") as file:
    TOKEN = file.read()

SPECIAL_TAGS = ["add","edit","delete","alias","list","owner","search", "admin"]
VALID_NAME_CHARS = set("0123456789abcdefghijklmnopqrstuvwxyz_-")

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}.")

@bot.event
async def on_message(message: discord.Message):
    # Keep commands working
    if message.content.startswith(f"{bot.command_prefix}"):
        return await bot.process_commands(message)
    if message.author.bot:
        return
    if re.search("https:\/\/discord\.com\/channels\/\d+\/\d+\/\d+", message.content):
        link = re.search("https:\/\/discord\.com\/channels\/\d+\/\d+\/\d+", message.content)
        link = link.group()
        embed =  await create_message_embed(link)
        await message.reply(embed=embed)
    
@bot.command(name="tag")
async def tag(ctx):
    await get_tag(ctx)

@bot.command(name="t")
async def t(ctx):
    await get_tag(ctx)

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.ExpectedClosingQuoteError) or isinstance(error, commands.InvalidEndOfQuotedStringError) or isinstance(error, commands.UnexpectedQuoteError):
        return await get_tag(ctx)
    else:
        raise error

async def context_formatter(ctx):
    message = ctx.message.content
    message = message.split(" ")
    if len(message) != 1:
        tag = message[1].lower()
        message = message[2:]
    else:
        tag = None
    return tag, message

async def get_tag(ctx):
    tag, message = await context_formatter(ctx)
    if tag == None:
        return await ctx.reply(f":information_source: %t `{"|".join(SPECIAL_TAGS)}`")
    if tag in SPECIAL_TAGS:
        return await special_tag(ctx, tag, message)
    filepath =f"{DIR}/tags/{tag}.json"
    if not pathlib.Path(filepath).exists():
        return await ctx.reply(f":warning: Tag **{tag}** does not exist.")
    with open(filepath, "r") as file:
        data = json.load(file)
    if data["type"] == "message":
        link = data["message_link"]
        embed = await create_message_embed(link)
        return await ctx.reply(embed=embed)
    if data["type"] == "code":
        return await container(ctx, tag, message)

async def special_tag(ctx, tag, message):
    if tag == "add":
        await add_tag(ctx, message[0], message[1:])
    if tag == "edit":
        await edit_tag(ctx, message[0], message[1:])
    if tag == "delete":
        await delete_tag(ctx, message[0])
    if tag == "alias":
        await alias_tag(ctx, message[0], message[1])
    if tag == "list":
        await list_tag(ctx, message[0])
    if tag == "owner":
        await owner_tag(ctx, message[0])
    if tag == "search":
        await search_tag(ctx, message)

async def add_tag(ctx, tag_name, tag_body):
    tag_body = " ".join(tag_body)
    tag_name = tag_name.lower()
    filepath =f"{DIR}/tags/{tag_name}.json"
    if pathlib.Path(filepath).exists():
        with open(filepath, "r") as file:
            data = json.load(file)
        return await ctx.reply(f":warning: Tag **{tag_name}** already exists and is owned by <@{data["owner"]}>.")
    if any(char not in VALID_NAME_CHARS for char in tag_name):
        return await ctx.reply(f":warning: Tag name must consist of characters a-z, 0-9, _, or -. ")
    
    if re.match("https:\/\/discord\.com\/channels\/\d+\/\d+\/\d+", tag_body):
        tag = {"name":tag_name,"type":"message","aliases":[],"message_link":tag_body, "owner":str(ctx.author.id)}
        with open(filepath, "w") as file:
            json.dump(tag, file)

    if tag_body.startswith("```"):
        tag_body = tag_body[3:-3]
        if tag_body.startswith("py"):
            tag_body = tag_body[2:]
        if tag_body.startswith("thon"):
            tag_body =  tag_body[4:]
        tag = {"name":tag_name,"type":"code","aliases":[],"owner":str(ctx.author.id)}
        with open(filepath, "w") as file:
            json.dump(tag, file)
        with open(f"{filepath[:-5]}.py", "w") as file:
            file.write(tag_body)
    return await ctx.reply(f":white_check_mark: Created tag **{tag_name}**")
    
async def container(ctx, tag, message):
    args = [str(ctx.author.id), ctx.author.name, str(ctx.channel.id)]
    if not message == None:
        args.extend(message)
    docargs = ['docker', 'run', '--rm', '-v', f'{DIR}\\tags:/data/:ro', 'python', 'python', f'/data/{tag}.py']
    docargs.extend(args)
    try:
        result = subprocess.run(
            docargs,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=5
        )
        output = result.stdout
        
    except subprocess.CalledProcessError as e:
        output = e
    await ctx.reply(output)

async def create_message_embed(link):
        link_list = link.split("/")[5:]
        channel = bot.get_channel(int(link_list[0]))
        msg = await channel.fetch_message(int(link_list[1]))
        name = msg.author.name
        pfp = msg.author.avatar
        content = msg.content
        embed=discord.Embed(description=f"{content}\n\n[Jump to message]({link})")
        embed.set_author(name=name, icon_url=pfp)
        return embed
        

bot.run(TOKEN)