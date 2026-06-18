import discord, os, traceback
from discord.ext import commands
from utils.bot import bot
from modules import editing, message_embed
from utils import config, logger
from utils.utils import DIR
LOGGER = logger.Logger()

token = input("Paste bot token: ")
if not os.path.exists(f"{DIR}/TOKEN.txt"):
    with open(f"{DIR}/TOKEN.txt", "w") as file:
        file.write(token)
if len(config.server_config["bot_admins"]) == 0:
    admin = input("Paste user id for bot admin (optional): ")
    try:
        admin = int(admin)
        config.server_config["bot_admins"].append(admin)
        config.save_server_config()
    except:
        pass
with open(f"{DIR}/TOKEN.txt", "r") as file:
    TOKEN = file.read()

@bot.event
async def on_ready():
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
    return await message_embed.message_reply(message)

@bot.event
async def on_message_edit(previous: discord.Message, current: discord.Message):
    if previous.author.bot: return
    if previous.content == current.content: return
    await editing.new_edit(current)

@bot.event
async def on_message_delete(message: discord.Message):
    if message.author.bot: return
    await editing.new_edit(message, True)

@bot.event
async def on_command_error(ctx: commands.Context, error: Exception):
    if isinstance(error, commands.CommandInvokeError):
        if isinstance(error.original, RecursionError):
            return await ctx.reply("Error: Recursion limit reached.")
        else:
            await LOGGER.error("".join(traceback.format_exception(error)))
            raise error
    else:
        await LOGGER.error("".join(traceback.format_exception(error)))
        raise error

bot.run(TOKEN)
