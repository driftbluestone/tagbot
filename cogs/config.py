import discord, os, psutil
from discord import app_commands
from discord.ext import commands
from api import gui
from utils import config
from utils.utils import DIR

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Config(bot=bot))

class Config(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

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

    @diagnostics.command(name="ping", description=diagnostics.description)
    async def ping(self, interaction: discord.Interaction):
        interaction.response.send_message(f"Ping: {self.bot.latency*1000} ms")

    devops = app_commands.Group(name="devops", description="Bot admin only debug information")

    @devops.command(name="logs", description=devops.description)
    async def logs(self, interaction: discord.Interaction):
        if not interaction.user.id in config.server_config["bot_admins"]:
            return await interaction.response.send_message(":warning: No permission.", ephemeral=True)
        file = discord.File(f"{DIR}/data/.log")
        await interaction.response.send_message(file=file)

    @devops.command(name="ls", description=devops.description)
    async def ls(self, interaction: discord.Interaction):
        if not interaction.user.id in config.server_config["bot_admins"]:
            return await interaction.response.send_message(":warning: No permission.", ephemeral=True)
        await interaction.response.send_message(view=FileView(DIR))
    
    @devops.command(name="quit", description=devops.description)
    async def quit(self, interaction: discord.Interaction):
        if not interaction.user.id in config.server_config["bot_admins"]:
            return await interaction.response.send_message(":warning: No permission.", ephemeral=True)
        await interaction.response.send_message("Restarting bot...")
        await self.bot.close()

class FileView(gui.PageUI):
    def __init__(self, workdir, page: int = 1):
        dirlist = os.listdir(workdir)
        self.workdir = workdir
        super().__init__(data_transfer=workdir, element_count=len(dirlist), page=page)
        dirlist = dirlist[((self.page-1)*10):(self.page*10)]
        for dir in dirlist:
            fulldir = os.path.join(workdir, dir)
            buttonstyle = discord.ButtonStyle.blurple if os.path.isfile(fulldir) else discord.ButtonStyle.secondary
            button = discord.ui.Button(label=dir, style=buttonstyle, custom_id=dir)
            button.callback = self.button_callback
            self.add_item(button)
        button = discord.ui.Button(label="..", style=discord.ButtonStyle.secondary, custom_id="..", row=4)
        button.callback = self.button_callback
        self.add_item(button)

    async def button_callback(self, interaction: discord.Interaction):
        if not interaction.user.id in config.server_config["bot_admins"]:
            return await interaction.response.send_message(":warning: No permission.", ephemeral=True)
        dir = interaction.data["custom_id"]
        fulldir = os.path.join(self.workdir, dir)
        await interaction.response.defer(thinking=False, ephemeral=True)
        if not os.path.isfile(fulldir):
            view = FileView(fulldir)
            await interaction.edit_original_response(view=view)
        else:
            await interaction.channel.send(file=discord.File(fulldir))
