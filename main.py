import discord, traceback
from discord.ext import commands
from modules import editing, message_embed
from utils import logger, utils
from utils.utils import bot
LOGGER = logger.Logger()

if len(utils.bot_config["bot_admins"]) == 0:
    admin = input("Paste user id for bot admin (optional): ")
    try:
        admin = int(admin)
        utils.bot_config["bot_admins"].append(admin)
        utils.save_bot_config()
    except:
        pass

@bot.event
async def on_ready():
    await LOGGER.info(f"Logged in as {bot.user}.")

@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        if bot.user.id != message.author.id:
            return
        if message.reference == None:
            return
        return await editing.create_reply_entry(message.id, message.reference.message_id)
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

bot.run(utils.data["TOKEN"])
