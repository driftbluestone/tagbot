import discord, pathlib
from discord.ext import commands
from modules import on_start
from modules.tags import tags
from modules.message_modules import editing, message_reply
from modules.config import *

class BOT(commands.Bot):
    def __init__(self):
        super().__init__(
        command_prefix="$",
        allowed_mentions=discord.AllowedMentions(
            users=False,
            everyone=False,
            roles=False,
            replied_user=True,
        ),
        intents=discord.Intents.all()
        )
    async def setup_hook(self):
        await self.load_extension("cogs.config")
        await self.load_extension("cogs.logs")
        await self.load_extension("cogs.boards")
bot = BOT()

DIR = pathlib.Path(__file__).resolve().parent

with open(f"{DIR}/TOKEN.txt", "r") as file:
    TOKEN = file.read()

@bot.event
async def on_ready():
    await on_start.on_ready()

    # sync all commands to discord
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} commands.")
    except Exception as exception:
        print(f"Error syncing commands: {exception}")
    print(f"Logged in as {bot.user}.")

@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        if message.reference == None: return
        return await editing.create_reply_json(message.id, message.reference.message_id)
    return await message_reply.message_reply(message, bot)
    
@bot.event
async def on_message_edit(previous: discord.Message, current: discord.Message):
    if previous.author.bot: return
    if previous.content == current.content: return
    await editing.new_edit(current, bot)
    
@bot.event
async def on_message_delete(message: discord.Message):
    if message.author.bot: return
    await editing.new_edit(message, bot, True)
    
@bot.command(name="tag")
async def tag(ctx):
    await tags.context_formatter(ctx)

@bot.command(name="t")
async def t(ctx):
    await tags.context_formatter(ctx)

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.ExpectedClosingQuoteError) or isinstance(error, commands.InvalidEndOfQuotedStringError) or isinstance(error, commands.UnexpectedQuoteError):
        return await tags.context_formatter(ctx)
    else:
        raise error

bot.run(TOKEN)