import discord, json, os, re, subprocess, pathlib, uuid
from discord.ext import commands
from dataclasses import asdict
from modules import tags, sed
from modules.message_embed import create_message_embed
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
    
    # check if message contains message link
    if re.search("https:\/\/discord\.com\/channels\/\d+\/\d+\/\d+", message.content):
        link = re.search("https:\/\/discord\.com\/channels\/\d+\/\d+\/\d+", message.content)
        link = link.group()
        embed =  await create_message_embed(link, bot)
        await message.reply(embed=embed)
    
    #sed command
    if message.content.startswith("sed/"):
        await sed.sed(message)
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