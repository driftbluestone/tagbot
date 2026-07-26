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
        try:
            synced = await self.tree.sync()
            print(f"Synced {len(synced)} commands.")
        except Exception as e:
            print(f"Error syncing commands: {e}")

        # load extensions
        await self.load_extension("cogs.extensions")

bot = _BOT()
