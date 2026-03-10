import discord
from discord.ext import commands
from modules.message_modules import editing
from modules.config import server_config

class Boards(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    async def get_channel(self, action):
        if action not in server_config["logged_actions"]: return False
        if server_config["logged_actions"][action] == 0: return False
        channel = await self.bot.fetch_channel(server_config["logged_actions"][action])
        return channel
    
    @commands.Cog.listener()
    async def on_reaction_add(self, reaction: discord.Reaction, user: discord.Member):
        if reaction.emoji not in server_config["boards"].keys(): return
        if reaction.count != server_config["boards"][reaction.emoji][1]: return
        channel = await self.bot.fetch_channel(server_config["boards"][reaction.emoji][0])
        await reaction.message.forward(channel)

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Boards(bot=bot))