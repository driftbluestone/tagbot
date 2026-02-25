# requires external packages discord and levenshtein, as well as docker
import discord, os, pathlib
from discord.ext import commands
from modules import tags, sed, sonny, message_embed
from modules.config import *
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
channel = 0
if not os.path.isdir(f"{DIR}/tags"):
    os.mkdir(f"{DIR}/tags")
if not os.path.isdir(f"{DIR}/users"):
    os.mkdir(f"{DIR}/users")

with open(f"{DIR}/TOKEN.txt", "r") as file:
    TOKEN = file.read()

@bot.event
async def on_ready():
    global channel
    channel = await bot.fetch_channel(server_config["edit_delete_log_channel"])
    print(f"Logged in as {bot.user}.")

@bot.event
async def on_message(message: discord.Message):
    
    # Keep commands working
    if message.content.startswith(f"{bot.command_prefix}"):
        return await bot.process_commands(message)
    if message.author.bot:
        return
    # sonny react
    await sonny.sonny(message)
    # check if message contains message link
    await message_embed.check_link(message, bot)
    
    #sed command
    if message.content.startswith("sed/"):
        await sed.sed(message)

@bot.event
async def on_message_edit(previous: discord.Message, current: discord.Message):
    if previous.author.bot:
        return
    prev = previous.content
    cur = current.content
    embed = discord.Embed(title=f"Message edited in <#{previous.channel.id}>", description=f"**Before:** `{prev}`\n**After:** `{cur}`\n[Jump to message]({current.jump_url})")
    embed.timestamp = previous.created_at
    embed.set_footer(text=f"ID: {current.id}")
    embed.set_author(name=previous.author.name, icon_url=previous.author.avatar)
    await channel.send(embed=embed)

@bot.event
async def on_message_delete(message: discord.Message):
    if message.author.bot:
        return
    content = message.content
    embed = discord.Embed(title=f"Message deleted in <#{message.channel.id}>", description=f"**Content:** `{content}`")
    embed.timestamp = message.created_at
    embed.set_footer(text=f"ID: {message.id}")
    embed.set_author(name=message.author.name, icon_url=message.author.avatar)
    await channel.send(embed=embed)
    

@bot.command(name="tag")
async def tag(ctx):
    await tags.context_formatter(ctx, bot)

@bot.command(name="t")
async def t(ctx):
    await tags.context_formatter(ctx, bot)

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.ExpectedClosingQuoteError) or isinstance(error, commands.InvalidEndOfQuotedStringError) or isinstance(error, commands.UnexpectedQuoteError):
        return await tags.context_formatter(ctx, bot)
    else:
        raise error

bot.run(TOKEN)