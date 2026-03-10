import discord, pathlib, typing
from discord import app_commands
from discord.ext import commands
from modules import config
from modules.tags import users
from modules.message_modules import boards

DIR = pathlib.Path(__file__).parent.absolute()
class Config(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="logging", description="Configure which channels which logs are sent to")
    async def channel(self, interaction: discord.Interaction):
        if not await users.permission_check(interaction.user, "log_admin"): return await interaction.response.send_message(":warning: No permission.",ephemeral=True)
        await interaction.response.send_message(view=config.ConfigButton(interaction))
    @app_commands.command(name="permissions", description="Configure user permissions")
    async def permissions(self, interaction: discord.Interaction, user: typing.Optional[discord.Member]):
        if not await users.permission_check(interaction.user, "edit_permissions"): return await interaction.response.send_message(":warning: No permission.",ephemeral=True)
        if user == None: user = interaction.user
        await interaction.response.send_message(content = f"Permissions for: {user.mention}",view=users.PermissionPanel(interaction, user))
    @app_commands.command(name="boards", description="Manage emoji-boards (ex. starboard)")
    async def boards(self, interaction: discord.Interaction):
        if not await users.permission_check(interaction.user, "manage_boards"): return await interaction.response.send_message(":warning: No permission.",ephemeral=True)
        await interaction.response.send_message(view=boards.BoardMaster(interaction))

async def setup(bot: commands.Bot) -> None:
    # finally, adding the cog to the bot
    await bot.add_cog(Config(bot=bot))