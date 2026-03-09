import discord, pathlib, typing
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
        if not await users.permission_check(interaction.user, "log_admin"): return await interaction.response.send_message(":warning: No permission.",ephemeral=True)
        await interaction.response.send_message(view=config.ConfigButton(interaction))
    @app_commands.command(name="permissions", description="Configure user permissions")
    async def permissions(self, interaction: discord.Interaction, user: typing.Optional[discord.User]):
        if not await users.permission_check(interaction.user, "edit_permissions"): return await interaction.response.send_message(":warning: No permission.",ephemeral=True)
        if user == None: user = interaction.user
        await interaction.response.send_message(view=users.PermissionPanel(interaction, user))

async def setup(bot: commands.Bot) -> None:
    # finally, adding the cog to the bot
    await bot.add_cog(Config(bot=bot))