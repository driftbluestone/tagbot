import discord, os, asyncio, importlib, json, sys
from discord import app_commands
from discord.ext import commands
from modules import uninstall_extension
from modules.bot import bot
from api import gui
from utils.config import server_config, save_server_config
from utils.logger import log

from pathlib import Path
DIR = Path(__file__).resolve().parent.parent

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Extensions(bot=bot))
    await load_extensions()

class Extensions(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    extension = app_commands.Group(name="extension", description="Manage extensions")

    @extension.command(name="toggle", description="Toggle extensions")
    async def extension_toggle(self, interaction: discord.Interaction):
        if not interaction.user.id in server_config["bot_admins"]:
            return await interaction.response.send_message(":warning: No permission.", ephemeral=True)
        view = ExtensionManager(interaction)
        return await interaction.response.send_message(view=view)

    @extension.command(name="add", description="Install extensions")
    async def extension_add(self, interaction: discord.Interaction, repo: str):
        if not interaction.user.id in server_config["bot_admins"]:
            return await interaction.response.send_message(":warning: No permission.", ephemeral=True)
        if not repo.startswith("https://github.com/"):
            return await interaction.response.send_message(f":warning: Please specify a git repo", ephemeral=True)

        repo_name = repo.split("/")[-1]
        if os.path.isdir(f"{DIR}/extensions/{repo_name}"):
            return await log("Extension already installed.")
        os.mkdir(f"{DIR}/extensions/{repo_name}")
        await interaction.response.send_message("Installing...")
        await Installer(interaction, repo).install_extension()
        await load_extensions()
        

    @extension.command(name="delete", description="Uninstall extensions")
    async def extension_delete(self, interaction: discord.Interaction, extension: str, save_data: bool):
        if not interaction.user.id in server_config["bot_admins"]:
            return await interaction.response.send_message(":warning: No permission.", ephemeral=True)
        if extension not in server_config["extensions"].keys():
            return await interaction.response.send_message(":warning: Extension not found.", ephemeral=True)
        await uninstall_extension.uninstall(interaction, bot, extension, save_data)

class Installer:
    def __init__(self, interaction: discord.Interaction, repo: str):
        self.extension = repo.split("/")[-1]
        self.repo = repo
        self.ext = self.extension
        self.interaction = interaction

    async def subprocess(self, args: list) -> str:
        try:
            result = await asyncio.create_subprocess_exec(
                *args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT
            )
            stdout, _ = await result.communicate()
            return stdout.decode()
        except Exception as e:
            return str(e)

    async def install_extension(self):
        await log(f"Cloning {self.extension} from {self.repo}...", self.interaction)
        output = await self.subprocess(["git", "clone", self.repo, f"{DIR}/extensions/{self.extension}"])
        await log(output.strip(), self.interaction)
        await self.dependencies()

    async def dependencies(self):
        filepath = f"{DIR}/extensions/{self.extension}/dependencies.json"
        if not os.path.exists(filepath):
            await log(f"Installed {self.ext}.", self.interaction)
            return

        with open(filepath, "r") as file:
            requirements = json.load(file)

        if "pip" in requirements:
            for pip in requirements["pip"]:
                await self.install_pip(pip)

        if "extension" in requirements:
            for extension in requirements["extension"]:
                self.extension = extension
                await log(f"Extension dependency found: {extension}. Installing...", self.interaction)
                await self.install_extension()
                await log(f"Extension dependency installed: {extension}.", self.interaction)

        if "other" in requirements:
            for other in requirements["other"]:
                await log(f"Other dependency '{other}' requires manual installation.", self.interaction)

        await log(f"Installed {self.ext} from {self.repo}.", self.interaction)

    async def install_pip(self, pip: str):
        await log(f"Installing pip dependency: {pip}...", self.interaction)
        output = await self.subprocess(["python3", "-m", "pip", "install", pip])
        await log(output.strip(), self.interaction)
        await log(f"Pip dependency installed: {pip}.", self.interaction)
    

class ExtensionManager(gui.MenuGUI):
    """Manage which extensions are enabled or disabled via /extension toggle"""
    def __init__(self, interaction, page = 1):
        super().__init__(interaction=interaction, element_count=len(server_config["extensions"].keys()), page=page)
        extensions = list(server_config["extensions"].keys())
        extensions = extensions[((self.page-1)*10):(self.page*10)]
        for extension in extensions:
            buttonstyle = discord.ButtonStyle.success if server_config["extensions"][extension] else discord.ButtonStyle.danger
            button = discord.ui.Button(label = extension, style=buttonstyle, custom_id=extension)
            button.callback = self.button_callback
            self.add_item(button)

    async def button_callback(self, interaction: discord.Interaction):
        if not interaction.user.id in server_config["bot_admins"]:
            return await interaction.response.send_message(":warning: No permission." ,ephemeral=True)
        extension = interaction.data["custom_id"]
        server_config["extensions"][extension] = not server_config["extensions"][extension]
        state = "enabled" if server_config["extensions"][extension] else "disabled"
        view = ExtensionManager(self.interaction, self.page)
        await interaction.response.defer(ephemeral=True, thinking=False)
        await self.interaction.edit_original_response(view=view)

        if server_config["extensions"][extension]:
            await reload_modules(extension)
            await bot.load_extension(f"extensions.{extension}.main")
        else:
            await bot.unload_extension(f"extensions.{extension}.main")
        await resync_commands()

        await log(f"Extension '{extension}' {state}.")
        save_server_config()

async def load_extensions():
    for i in os.listdir(f"{DIR}/extensions"):
        if i not in server_config["extensions"]:
            server_config["extensions"][i] = True
            try:
                os.mkdir(f"{DIR}/data/extensions/{i}")
            except FileExistsError:
                pass
            if os.path.exists(f"{DIR}/extensions/{i}/init.py"):
                importlib.import_module(f"extensions.{i}.init")
            save_server_config()
            await log(f"Registered new extension: {i}.")

        if server_config["extensions"][i]:
            try:
                await reload_modules(i)
                await bot.load_extension(f"extensions.{i}.main")
                await log(f"Loaded extension: {i}.")
            except Exception as e:
                await log(f"Failed to load extension {i}: {e}")
        else:
            try:
                await bot.unload_extension(f"extensions.{i}.main")
                await log(f"Unloaded extension: {i}.")
            except:
                pass
    await resync_commands()

async def resync_commands():
    try:
        synced = await bot.tree.sync()
        await log(f"Synced {len(synced)} commands.")
    except Exception as e:
        await log(f"Failed to sync commands: {e}")

async def reload_modules(extension_name: str):
    extension_prefix = f"extensions.{extension_name}"
    for module_name in list(sys.modules.keys()):
        if module_name == f"{extension_prefix}.main":
            continue
        elif module_name.startswith(extension_prefix):
            sys.modules.pop(module_name, None)