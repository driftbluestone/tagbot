import discord, pathlib
from discord import app_commands
from discord.ext import commands
from modules.message_modules import logging
from modules.config import server_config
DIR = pathlib.Path(__file__).parent.absolute()
class Logging(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message_edit(self, previous: discord.Message, current: discord.Message):
        if previous.author.bot: return
        if previous.content == current.content: return
        channel = self.bot.fetch_channel(server_config["logged_actions"]["edit_message"])
        await logging.edit_message(previous, current, channel)
    
    @commands.cog.listener()
    async def on_message_delete(self, message: discord.Message):
        if message.author.bot:return
        channel = self.bot.fetch_channel(server_config["logged_actions"]["delete_message"])
        await logging.delete_message(message, channel)
    
async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Logging(bot=bot))