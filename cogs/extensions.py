import discord, pathlib, os, math, subprocess, shutil, stat
from discord import app_commands
from discord.ext import commands
from modules import config
from modules.config import server_config
DIR = pathlib.Path(__file__).resolve().parent

class Extensions(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    extension = app_commands.Group(name="extension", description="Magage Extenions")
    @extension.command(name="toggle")
    async def extension_toggle(self, interaction: discord.Interaction):
        if not interaction.user.id in server_config["bot_admins"]: return await interaction.response.send_message(":warning: No permission.",ephemeral=True)
        view = ExtensionManager(interaction, self.bot)
        return await interaction.response.send_message(view=view)
    
    @extension.command(name="add")
    async def extension_add(self, interaction: discord.Interaction, repo: str):
        if not interaction.user.id in server_config["bot_admins"]: return await interaction.response.send_message(":warning: No permission.",ephemeral=True)
        if not repo.startswith("https://github.com/"): return await interaction.response.send_message(f":warning: Please specify a git repo",ephemeral=True)
        
        repo_name = repo.split("/")[-1]
        if os.path.isdir(f"{DIR}/../extensions/{repo_name}"): shutil.rmtree(f'{DIR}/../extensions/{repo_name}')
        os.mkdir(f"{DIR}/../extensions/{repo_name}")
        args = ["git", "clone", repo, f"{DIR}/../extensions/{repo_name}"]
        try:
            result = subprocess.run(
                args,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )
            output = result.stdout
        except subprocess.CalledProcessError as e:
            output = str(e)
        server_config["extensions"][repo_name] = True
        await load_extensions(self.bot)
        return await interaction.response.send_message(content=f"Sucessfully added module {repo_name}!\n{output}")
    
    @extension.command(name="delete")
    async def extension_delete(self, interaction: discord.Interaction, extension: str):
        if not interaction.user.id in server_config["bot_admins"]: return await interaction.response.send_message(":warning: No permission.",ephemeral=True)
        if extension not in server_config["extensions"].keys(): return await interaction.response.send_message(":warning: Extension not found.",ephemeral=True)
        server_config["extensions"].pop(extension)
        try: await self.bot.unload_extension(f"extensions.{extension}.main")
        except: pass
        shutil.rmtree(f'{DIR}/../extensions/{extension}', onexc=remove_readonly)
        await interaction.response.send_message(f":white_check_mark: Extension **{extension}** deleted.")

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Extensions(bot=bot))
    await load_extensions(bot)

def remove_readonly(func, path, _):
    """Clear the read-only and hidden attributes and retry removal."""
    os.chmod(path, stat.S_IWRITE)
    func(path)

class ExtensionManager(discord.ui.View):
    """Manage which extensions are enabled or disabled via /extension toggle"""
    def __init__(self, old_interaction, bot, page = 1):
        super().__init__(timeout=None)
        self.old_interaction: discord.Interaction = old_interaction
        self.page = page
        self.bot = bot
        extensions = list(server_config["extensions"].keys())
        extensions = extensions[((page-1)*10):(page*10)]
        for extension in extensions:
            buttonstyle = discord.ButtonStyle.danger
            if server_config["extensions"][extension]: buttonstyle = discord.ButtonStyle.success
            button = discord.ui.Button(label = extension, style=buttonstyle, custom_id=extension)
            button.callback = self.open_modal_button_callback
            self.add_item(button)
        self.max_page = math.ceil(len(server_config["logs"].keys())/10)
        config.page_select_buttons(self, page)

    async def open_modal_button_callback(self, interaction: discord.Interaction):
        if not interaction.user.id in server_config["bot_admins"]: return await interaction.response.send_message(":warning: No permission.",ephemeral=True)
        old_interaction = self.old_interaction
        extension = interaction.data["custom_id"]
        server_config["extensions"][extension] = not server_config["extensions"][extension]
        view = ExtensionManager(old_interaction, self.bot, self.page)
        await old_interaction.edit_original_response(view=view)
        await load_extensions(self.bot)
        await interaction.response.defer(ephemeral=True, thinking=False)

    async def page_selector(self, interaction: discord.Interaction):
        if not interaction.user.id in server_config["bot_admins"]: return await interaction.response.send_message(":warning: No permission.",ephemeral=True)
        await config.select_page(interaction, self.old_interaction, self.page, self.max_page, ExtensionManager, self.bot)

async def load_extensions(bot: commands.Bot):
    for i in os.listdir(f"{DIR}/../extensions"):
        if server_config["extensions"][i]:
            try: await bot.load_extension(f"extensions.{i}.main")
            except Exception as e:
                raise e
        else:
            try: await bot.unload_extension(f"extensions.{i}.main")
            except: pass
