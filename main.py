# requires external packages discord and levenshtein, as well as docker
import discord, os, pathlib
from discord.ext import commands
from modules import message_reply, message_reply, tags, logging, editing, message_reply
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
if not os.path.isdir(f"{DIR}/history"):
    os.mkdir(f"{DIR}/history")

with open(f"{DIR}/TOKEN.txt", "r") as file:
    TOKEN = file.read()

@bot.event
async def on_ready():
    global channel
    channel = await bot.fetch_channel(server_config["edit_delete_log_channel"])
    print(f"Logged in as {bot.user}.")

@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        if message.reference == None: return
        return await editing.create_reply_json(message.id, message.reference.message_id)
    return await message_reply.message_reply(message, bot)
    
@bot.event
async def on_message_edit(previous: discord.Message, current: discord.Message):
    if previous.author.bot:
        return
    await logging.edit_message(previous, current, channel)
    await editing.new_edit(current, bot)
    
@bot.event
async def on_message_delete(message: discord.Message):
    if message.author.bot:
        return
    await logging.delete_message(message, channel)
    await editing.new_edit(message, bot)
    
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