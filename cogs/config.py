import discord, pathlib, typing, os, psutil
from discord import app_commands
from discord.ext import commands
from utils import users, config
from modules.permission_panel import PermissionPanel
async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Config(bot=bot))

DIR = pathlib.Path(__file__).absolute().parent.parent
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

    @diagnostics.command(name="ram", description=diagnostics.description)
    async def ram(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"{psutil.Process(os.getpid()).memory_info().rss /1024**2:.2f} MB")
    
    @diagnostics.command(name="cogs", description=diagnostics.description)
    async def cogs(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"{self.bot.cogs}")
    
    @diagnostics.command(name="member-count", description=diagnostics.description)
    async def member_count(self, interaction: discord.Interaction):
        await interaction.response.send_message(interaction.guild.member_count)
    
    @diagnostics.command(name="commands", description=diagnostics.description)
    async def commands(self, interaction: discord.Interaction):
        commands = [command.name for command in list(self.bot.commands)]
        commands.remove("help")
        commands += [command.name for command in self.bot.tree.walk_commands()]
        await interaction.response.send_message(commands)

    @diagnostics.command(name="logs", description=diagnostics.description)
    async def logs(self, interaction: discord.Interaction):
        if not interaction.user.id in config.server_config["bot_admins"]:
            return await interaction.response.send_message(":warning: No permission.", ephemeral=True)
        file = discord.File(f"{DIR}/data/.log")
        await interaction.response.send_message(file=file)