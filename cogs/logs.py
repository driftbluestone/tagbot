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
        channel = await self.get_channel("edit_message")
        if channel == False: return
        await logging.edit_message(previous, current, channel)

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        if message.author.bot: return
        channel = await self.get_channel("delete_message")
        if channel == False: return
        await logging.delete_message(message, channel)

    @commands.Cog.listener()
    async def on_guild_channel_create(self, guild_channel: discord.ChannelType):
        channel = await self.get_channel("create_channel")
        if channel == False: return
        await logging.create_delete_channel(guild_channel, channel, ["Created", "New"])
    
    @commands.Cog.listener()
    async def on_guild_channel_delete(self, guild_channel: discord.ChannelType):
        channel = await self.get_channel("delete_channel")
        if channel == False: return
        await logging.create_delete_channel(guild_channel, channel, ["deleted", "Deleted"])

    @commands.Cog.listener()
    async def on_audit_log_entry_create(self, entry: discord.AuditLogEntry):
        channel = await self.get_channel(entry.action.name)
        if channel == False: return
        await logging.audit_log_entry(entry, channel)

    
    
async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Logging(bot=bot))