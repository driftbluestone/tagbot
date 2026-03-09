import discord, pathlib
from discord import app_commands
from discord.ext import commands
from modules import config
from modules.tags import users

DIR = pathlib.Path(__file__).parent.absolute()
class Config(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="logging", description="Configure which channels which logs are sent to")
    async def channel(self, interaction: discord.Interaction):
        if not await users.permission_check(interaction.user, "logmaster"): return await interaction.response.send_message(":warning: No permission.",ephemeral=True)
        await interaction.response.send_message(view=config.ConfigButton(interaction))

async def setup(bot: commands.Bot) -> None:
    # finally, adding the cog to the bot
    await bot.add_cog(Config(bot=bot))