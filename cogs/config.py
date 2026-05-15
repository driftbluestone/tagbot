import discord, pathlib, typing, os, psutil
from discord import app_commands
from discord.ext import commands
from utils import users
from modules.permission_panel import PermissionPanel
async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Config(bot=bot))

DIR = pathlib.Path(__file__).parent.absolute()
class Config(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="permissions", description="Configure user permissions")
    async def permissions(self, interaction: discord.Interaction, user: typing.Optional[discord.Member]):
        if not await users.permission_check(interaction.user.id, "edit_permissions"):
            return await interaction.response.send_message(":warning: No permission.", ephemeral=True)
        if user == None: user = interaction.user
        await interaction.response.send_message(content = f"Permissions for: {user.mention}",view=PermissionPanel(interaction, user))
    
    diagnostics = app_commands.Group(name="diagnostics", description="View bot information")

    @diagnostics.command(name="ram")
    async def ram(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"{psutil.Process(os.getpid()).memory_info().rss /1024**2:.2f} MB")
    
    @diagnostics.command(name="cogs")
    async def cogs(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"{self.bot.cogs}")
    
    @diagnostics.command(name="member-count")
    async def member_count(self, interaction: discord.Interaction):
        await interaction.response.send_message(interaction.guild.member_count)
    
    @diagnostics.command(name="commands")
    async def commands(self, interaction: discord.Interaction):
        commands = [command.name for command in list(self.bot.commands)]
        commands.remove("help")
        commands += [command.name for command in self.bot.tree.walk_commands()]
        await interaction.response.send_message(commands)