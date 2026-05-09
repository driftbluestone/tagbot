import discord, pathlib
from discord.ext import commands
from modules.bot import bot
from modules import editing
from utils import message_embed

DIR = pathlib.Path(__file__).resolve().parent

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
async def on_command_error(ctx: commands.Context, error):
    if isinstance(error, commands.CommandInvokeError):
        if isinstance(error.original, RecursionError):
            return await ctx.reply("Error: Recursion limit reached.")
        else:
            raise error
    else:
        raise error

bot.run(TOKEN)