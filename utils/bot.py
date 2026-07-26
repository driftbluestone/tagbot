import discord
from discord.ext import commands
from modules import on_start
from utils.config import bot_config

__all__ = ["bot"]

class _BOT(commands.Bot):
    def __init__(self):
        super().__init__(
        command_prefix=bot_config["command_prefix"],
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
        await self.load_extension("cogs.permissions")
        await self.load_extension("cogs.extensions")

bot = _BOT()
