import discord
from discord.ext import commands
from modules.message_modules import logging
from modules.config import server_config

class Logging(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    async def get_channel(self, action):
        if action not in server_config["logged_actions"]: return False
        if server_config["logged_actions"][action] == 0: return False
        channel = self.bot.get_partial_messageable(server_config["logged_actions"][action])
        return channel
    
    @commands.Cog.listener()
    async def on_message_edit(self, previous: discord.Message, current: discord.Message):
        if previous.author.bot: return
        if previous.content == current.content: return
        channel = await self.get_channel("messege_edit")
        if channel == False: return
        await logging.edit_message(previous, current, channel)

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        if message.author.bot: return
        channel = await self.get_channel("messege_delete")
        if channel == False: return
        await logging.delete_message(message, channel)

    @commands.Cog.listener()
    async def on_audit_log_entry_create(self, entry: discord.AuditLogEntry):
        if entry.action.name == "message_delete": return
        channel = await self.get_channel(entry.action.name)
        if channel == False: return
        await logging.audit_log_entry(entry, channel)

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Logging(bot=bot))