import discord
from discord.ext import commands
from modules import on_start
from utils.server_config import server_config

class _BOT(commands.Bot):
    def __init__(self):
        on_start.on_ready()
        super().__init__(
        command_prefix=server_config["command_prefix"],
        case_insensitive=True,
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
        await self.load_extension("cogs.extensions")
bot = _BOT()
