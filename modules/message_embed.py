import discord, re
from api import gui
from utils.utils import bot

async def message_reply(message: discord.Message):
    # Keep commands working
    if message.content.startswith(f"{bot.command_prefix}"):
        return await bot.process_commands(message)
    # check if message contains message link
    link = re.search(r"https:\/\/discord\.com\/channels\/\d+\/\d+\/\d+", message.content)
    if link:
        link = re.search(r"https:\/\/discord\.com\/channels\/\d+\/\d+\/\d+", message.content)
        link = link.group()
        embed =  await gui.create_message_embed(link)
        if embed == None: return
        await message.reply(embed=embed)
