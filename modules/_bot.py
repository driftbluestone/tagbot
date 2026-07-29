import discord
from discord.ext import commands
from db import db

class BOT(commands.Bot):
    def __init__(self):
        super().__init__(
        command_prefix=get_prefix,
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

def get_prefix(bot: commands.Bot, message: discord.Message):
    prefix = db.get("server", (message.guild.id,), ("server_id",), ("command_prefix",))
    if prefix is None:
        return '%'
    return prefix