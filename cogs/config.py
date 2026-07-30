import discord, os, psutil
from discord import app_commands
from discord.ext import commands
from api import gui
from db import db, users
from utils.utils import DIR, bot_config

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Config(bot=bot))

class Config(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    diagnostics = app_commands.Group(name="diagnostics", description="View bot information")

    @diagnostics.command(name="ram", description=diagnostics.description)
    async def ram(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"{psutil.Process(os.getpid()).memory_info().rss /1024**2:.2f} MB")

    @diagnostics.command(name="extensions", description=diagnostics.description)
    async def cogs(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"{self.bot.extensions}")

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
        await interaction.response.send_message(f"Ping: {round(self.bot.latency*1000)} ms")

    class Customize(app_commands.Group):
            async def interaction_check(self, interaction: discord.Interaction):
                if await users.check_permission(interaction.guild.id, interaction.user.id, "#:manage_extensions"):
                    return True
                await interaction.response.send_message(":warning: No permission.", ephemeral=True)
                return False

    customize = Customize(name="customize", description="Customize your bot")

    @customize.command(name="avatar", description="Change avatar")
    async def avatar(self, interaction: discord.Interaction, image: discord.Attachment):
        if not image.content_type or not image.content_type.startswith("image/"):
            return await interaction.response.send_message("Please upload a valid image file (PNG/JPEG).", ephemeral=True)

        try:
            await interaction.guild.me.edit(avatar=await image.read())
        except discord.Forbidden:
            return await interaction.response.send_message("Bot missing `Change Nickname` permission.", ephemeral=True)
        return await interaction.response.send_message("Updated avatar.")

    @customize.command(name="nick", description="Change display name")
    async def nick(self, interaction: discord.Interaction, name: str):
        try:
            await interaction.guild.me.edit(nick=name)
        except discord.Forbidden:
            return await interaction.response.send_message("Bot missing `Change Nickname` permission.", ephemeral=True)
        return await interaction.response.send_message("Updated nickname.")

    @customize.command(name="bio", description="Change bio")
    async def bio(self, interaction: discord.Interaction, bio: str):
        await interaction.guild.me.edit(bio=bio)
        return await interaction.response.send_message("Updated bio.")

    @customize.command(name="banner", description="Change banner")
    async def banner(self, interaction: discord.Interaction, image: discord.Attachment):
        if not image.content_type or not image.content_type.startswith("image/"):
            return await interaction.response.send_message("Please upload a valid image file (PNG/JPEG).", ephemeral=True)
        
        await interaction.guild.me.edit(banner=await image.read())
        return await interaction.response.send_message("Updated avatar.")

    @customize.command(name="prefix", description="Change command prefix")
    async def prefix(self, interaction: discord.Interaction, prefix: str):
        db.insert("server", ("server_id",), ("command_prefix",), (interaction.guild.id, prefix))
        return await interaction.response.send_message("Updated command prefix.")

    class DevDiagnostics(app_commands.Group):
        async def interaction_check(self, interaction: discord.Interaction):
            if interaction.user.id in bot_config["bot_admins"]:
                return True
            await interaction.response.send_message(":warning: No permission.", ephemeral=True)
            return False

    botadmin = DevDiagnostics(name="botadmin", description="Bot admin only debug information")

    @botadmin.command(name="logs", description=botadmin.description)
    async def logs(self, interaction: discord.Interaction):
        file = discord.File(f"{DIR}/data/.log")
        await interaction.response.send_message(file=file)

    @botadmin.command(name="ls", description=botadmin.description)
    async def ls(self, interaction: discord.Interaction):
        await interaction.response.send_message(view=FileView(DIR))

    @botadmin.command(name="invite", description="Send invite to user")
    async def invite(self, interaction: discord.Interaction, user: discord.Member):
        permissions = discord.Permissions(
            change_nickname=True,
            view_audit_log=True,
            read_messages=True,
            send_messages=True,
            embed_links=True,
            attach_files=True,
            read_message_history=True,
            administrator=True
        )
        
        url = discord.utils.oauth_url(self.bot.user.id, permissions=permissions)
        await user.send(content=f"Invite {self.bot.user.name} to your server with this link: {url}")
        setattr(self.bot, "allowed_joins", getattr(self.bot, "allowed_joins", 0)+1)
        return await interaction.response.send_message("Invite sent!")
    
    @botadmin.command(name="quit", description=botadmin.description)
    async def quit(self, interaction: discord.Interaction):
        await interaction.response.send_message("Quitting bot...")
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
        if not interaction.user.id in bot_config["bot_admins"]:
            return await interaction.response.send_message(":warning: No permission.", ephemeral=True)
        dir = interaction.data["custom_id"]
        fulldir = os.path.join(self.workdir, dir)
        await interaction.response.defer(thinking=False, ephemeral=True)
        if not os.path.isfile(fulldir):
            view = FileView(fulldir)
            await interaction.edit_original_response(view=view)
        else:
            await interaction.channel.send(file=discord.File(fulldir))
