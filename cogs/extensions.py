import discord, os, asyncio, importlib, sys, shutil, typing
from discord import app_commands
from discord.ext import commands
from utils.bot import bot
from utils import config, jsonIO
from utils.logger import Logger
LOGGER = Logger()
from api import gui
from pathlib import Path
from utils.utils import DIR

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Extensions(bot=bot))
    await load_extensions()

class Extensions(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    extension = app_commands.Group(name="extension", description="Manage extensions")

    @extension.command(name="toggle", description="Toggle extensions")
    async def extension_toggle(self, interaction: discord.Interaction):
        if not interaction.user.id in config.server_config["bot_admins"]:
            return await interaction.response.send_message(":warning: No permission.", ephemeral=True)
        view = ExtensionManager()
        return await interaction.response.send_message(view=view)

    @extension.command(name="update", description="Update extensions")
    async def extension_update(self, interaction: discord.Interaction, repo: str):
        if not interaction.user.id in config.server_config["bot_admins"]:
            return await interaction.response.send_message(":warning: No permission.", ephemeral=True)
        if not repo.startswith("https://github.com/"):
            return await interaction.response.send_message(f":warning: Please specify a git repo", ephemeral=True)
        repo_name = repo.split("/")[-1]
        if repo_name not in config.server_config["extensions"].keys():
            return await interaction.response.send_message(":warning: Extension not found.", ephemeral=True)
        await LOGGER.info(f"Updating extension {repo_name} from {repo}.", interaction)
        await uninstall(interaction, repo_name, True, True)
        await self.download_repo(interaction, repo, True)
        await LOGGER.info(f"Updated extension {repo_name} from {repo}.", interaction)

    @extension.command(name="add", description="Install extensions")
    async def extension_add(self, interaction: discord.Interaction, repo: str):
        if not interaction.user.id in config.server_config["bot_admins"]:
            return await interaction.response.send_message(":warning: No permission.", ephemeral=True)
        if not repo.startswith("https://github.com/"):
            return await interaction.response.send_message(f":warning: Please specify a git repo", ephemeral=True)
        await self.download_repo(interaction, repo)

    async def download_repo(self, interaction: discord.Interaction, repo: str, silent: bool = False):
        repo_name = repo.split("/")[-1]
        if os.path.isdir(f"{DIR}/extensions/{repo_name}"):
            return await LOGGER.warn("Extension already installed.", interaction)
        os.mkdir(f"{DIR}/extensions/{repo_name}")
        await Installer(None if silent else interaction, repo).install_extension()
        await load_extensions()

    @extension.command(name="delete", description="Uninstall extensions")
    async def extension_delete(self, interaction: discord.Interaction, extension: str, save_data: typing.Optional[bool] = True):
        if not interaction.user.id in config.server_config["bot_admins"]:
            return await interaction.response.send_message(":warning: No permission.", ephemeral=True)
        if extension not in config.server_config["extensions"].keys():
            return await interaction.response.send_message(":warning: Extension not found.", ephemeral=True)
        await uninstall(interaction, extension, save_data)

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
        # await log(f"Cloning {self.extension} from {self.repo}...", self.interaction)
        output = await self.subprocess(["git", "clone", self.repo, f"{DIR}/extensions/{self.extension}"])
        await LOGGER.info(output.strip(), self.interaction)
        if os.path.exists(Path(f"{DIR}/extensions/{self.extension}/main.py")):
            await LOGGER.info(f"Installed {self.extension}", self.interaction)
        else:
            await LOGGER.error(f"Failed to install {self.extension}", self.interaction)
            await uninstall(self.interaction, self.extension)
        await self.dependencies()

    async def dependencies(self):
        filepath = f"{DIR}/extensions/{self.extension}/dependencies.json"
        if not os.path.exists(filepath):
            return
        requirements = jsonIO.load(filepath)

        if "pip" in requirements:
            for pip in requirements["pip"]:
                await self.install_pip(pip)

        if "extension" in requirements:
            for extension in requirements["extension"]:
                self.extension = extension
                await LOGGER.info(f"Extension dependency found: {extension}. Installing...", self.interaction)
                await self.install_extension()
                await LOGGER.info(f"Extension dependency installed: {extension}.", self.interaction)

        if "other" in requirements:
            for other in requirements["other"]:
                await LOGGER.warn(f"Other dependency '{other}' requires manual installation.", self.interaction)

        await LOGGER.info(f"Installed {self.ext} from {self.repo}.", self.interaction)

    async def install_pip(self, pip: str):
        await LOGGER.info(f"Installing pip dependency: {pip}...", self.interaction)
        output = await self.subprocess(["python3", "-m", "pip", "install", pip])
        await LOGGER.info(output.strip(), self.interaction)
        await LOGGER.info(f"Pip dependency installed: {pip}.", self.interaction)

class ExtensionManager(gui.PageUI):
    """Manage which extensions are enabled or disabled via /extension toggle"""
    def __init__(self, _ = None, page = 1):
        super().__init__(element_count = len(config.server_config["extensions"].keys()), page = page)
        extensions = list(config.server_config["extensions"].keys())
        extensions = extensions[((self.page-1)*10):(self.page*10)]

        for extension in extensions:
            buttonstyle = discord.ButtonStyle.success if config.server_config["extensions"][extension] else discord.ButtonStyle.danger
            button = discord.ui.Button(label = extension, style=buttonstyle, custom_id=extension)
            button.callback = self.button_callback
            self.add_item(button)

    async def button_callback(self, interaction: discord.Interaction):
        if not interaction.user.id in config.server_config["bot_admins"]:
            return await interaction.response.send_message(":warning: No permission." ,ephemeral=True)
        extension = interaction.data["custom_id"]
        config.server_config["extensions"][extension] = not config.server_config["extensions"][extension]
        state = "enabled" if config.server_config["extensions"][extension] else "disabled"
        view = ExtensionManager(page = self.page)
        await interaction.response.defer(ephemeral=True, thinking=False)
        await interaction.message.edit(view=view)

        if config.server_config["extensions"][extension]:
            await reload_modules(extension)
            await bot.load_extension(f"extensions.{extension}.main")
        else:
            await bot.unload_extension(f"extensions.{extension}.main")
        await resync_commands()

        await LOGGER.info(f"Extension '{extension}' {state}.")
        config.save_server_config()

async def load_extensions():
    for i in os.listdir(f"{DIR}/extensions"):
        if i not in config.server_config["extensions"]:
            config.server_config["extensions"][i] = True
            try:
                os.mkdir(f"{DIR}/data/extensions/{i}")
            except FileExistsError:
                pass
            if os.path.exists(f"{DIR}/extensions/{i}/init.py"):
                importlib.import_module(f"extensions.{i}.init")
                config.save_server_config()
                await LOGGER.info(f"Registered new extension: {i}.")

        if config.server_config["extensions"][i]:
            try:
                await reload_modules(i)
                await bot.load_extension(f"extensions.{i}.main")
                await LOGGER.info(f"Loaded extension: {i}.")
            except Exception as e:
                await LOGGER.error(f"Failed to load extension {i}: {e}")
        else:
            try:
                await bot.unload_extension(f"extensions.{i}.main")
                await LOGGER.info(f"Unloaded extension: {i}.")
            except:
                pass
    await resync_commands()

async def resync_commands():
    try:
        synced = await bot.tree.sync()
        await LOGGER.info(f"Synced {len(synced)} commands.")
    except Exception as e:
        await LOGGER.error(f"Failed to sync commands: {e}")

async def reload_modules(extension_name: str):
    extension_prefix = f"extensions.{extension_name}"
    for module_name in list(sys.modules.keys()):
        if module_name == f"{extension_prefix}.main":
            continue
        elif module_name.startswith(extension_prefix):
            sys.modules.pop(module_name, None)

async def uninstall(interaction: discord.Interaction, extension: str, save_data: bool = True, silent: bool = False) -> None:
    def _remove_readonly(func, path, _):
        os.chmod(path, 128)
        func(path)

    config.server_config["extensions"].pop(extension)
    config.save_server_config()
    if not silent:
        await interaction.response.defer()
    try:
        await bot.unload_extension(f"extensions.{extension}.main")
    except:
        pass

    if not save_data:
        # remove permissions
        config.permissions_config
        permission_keys: list[str] = list(config.permissions_config.keys())
        for k in permission_keys:
            if k.startswith(extension + ":"):
                config.permissions_config.pop(k)
        config.save_permisions_config()

        # remove user fields
        user_keys: list[str] = list(config.user_config.keys())
        for k in user_keys:
            if k.startswith(extension + ":"):
                config.user_config.pop(k)
        config.save_user_config()
    # remove files
        shutil.rmtree(f'{DIR}/data/extensions/{extension}', onexc=_remove_readonly)
    shutil.rmtree(f'{DIR}/extensions/{extension}', onexc=_remove_readonly)
    if not silent:
        await LOGGER.info(f":white_check_mark: Extension **{extension}** deleted.")
