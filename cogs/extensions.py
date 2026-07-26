import discord, os, asyncio, importlib, sys, shutil, typing
from discord import app_commands
from discord.ext import commands
from psycopg import sql
from utils import config, jsonIO
from utils.bot import bot
from utils.utils import DIR
from utils.logger import Logger
LOGGER = Logger()
from db import db, server, user
from api import gui

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Extensions(bot=bot))
    await load_extensions()

class Extensions(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    extension = app_commands.Group(name="extension", description="Manage extensions")

    @extension.command(name="toggle", description="Toggle extensions")
    async def extension_toggle(self, interaction: discord.Interaction):
        if not user.check_permission(interaction.guild.id, interaction.user.id, "manage_extensions"):
            return await interaction.response.send_message(":warning: No permission.", ephemeral=True)
        view = ExtensionManager(interaction.guild)
        return await interaction.response.send_message(view=view)

    @extension.command(name="update", description="Requires bot admin. Update extensions")
    async def extension_update(self, interaction: discord.Interaction, repo: str):
        if interaction.user.id in config.bot_config["bot_admins"]:
            return await interaction.response.send_message(":warning: No permission.", ephemeral=True)
        if not repo.startswith("https://github.com/"):
            return await interaction.response.send_message(f":warning: Please specify a git repo", ephemeral=True)
        repo_name = repo.split("/")[-1]
        if repo_name not in config.bot_config["extensions"].keys():
            return await interaction.response.send_message(":warning: Extension not found.", ephemeral=True)
        await LOGGER.info(f"Updating extension {repo_name} from {repo}.", interaction)
        await uninstall(interaction, repo_name, True, True)
        await self.download_repo(interaction, repo, True)
        await LOGGER.info(f"Updated extension {repo_name} from {repo}.", interaction)

    @extension.command(name="add", description="Requires bot admin. Install extensions")
    async def extension_add(self, interaction: discord.Interaction, repo: str):
        if interaction.user.id in config.bot_config["bot_admins"]:
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

    @extension.command(name="delete", description="Requires bot admin. Uninstall extensions")
    async def extension_delete(self, interaction: discord.Interaction, extension: str, save_data: typing.Optional[bool] = True):
        if interaction.user.id in config.bot_config["bot_admins"]:
            return await interaction.response.send_message(":warning: No permission.", ephemeral=True)
        if extension not in config.bot_config["extensions"].keys():
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
        if os.path.exists(f"{DIR}/extensions/{self.extension}/main.py"):
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
    def __init__(self, guild: discord.Guild, page = 1):
        extensions = server.get(0, ("extensions",))
        server_extensions = server.get(guild.id, ("extensions",))
        self.extensions = {k: True if k in server_extensions else False for k in extensions}
        super().__init__(element_count = len(extensions), page = page, data_transfer=guild)
        
        extensions = extensions[((self.page-1)*10):(self.page*10)]

        for extension in extensions:
            buttonstyle = discord.ButtonStyle.success if self.extensions[extension] else discord.ButtonStyle.danger
            button = discord.ui.Button(label=extension, style=buttonstyle, custom_id=extension)
            button.callback = self.button_callback
            self.add_item(button)

    async def button_callback(self, interaction: discord.Interaction):
        if not user.check_permission(interaction.guild.id, interaction.user.id, "manage_extensions"):
            return await interaction.response.send_message(":warning: No permission.", ephemeral=True)
        extension = interaction.data["custom_id"]
        
        self.extensions[extension] = not self.extensions[extension]
        state = "enabled" if self.extensions[extension] else "disabled"
        extensions = [k for k, v in self.extensions.items() if v]
        server.update(interaction.guild.id, ("extensions",), (jsonIO.dumps(extensions),))
        view = ExtensionManager(self.data_transfer, self.page)
        await interaction.response.defer(ephemeral=True, thinking=False)
        await interaction.message.edit(view=view)

    # REWRITE REWRITE REWRITE
        if self.extensions[extension]:
            reload_modules(extension)
            await bot.load_extension(f"extensions.{extension}.main")
        else:
            await bot.unload_extension(f"extensions.{extension}.main")
        await resync_commands()

        await LOGGER.info(f"Extension '{extension}' {state}.")

async def load_extensions():
    for i in os.listdir(f"{DIR}/extensions"):
        if i not in config.bot_config["extensions"]:
            config.bot_config["extensions"][i] = True
            try:
                os.mkdir(f"{DIR}/extensions/{i}")
            except FileExistsError:
                pass
            if os.path.exists(f"{DIR}/extensions/{i}/init.py"):
                importlib.import_module(f"extensions.{i}.init")
                config.save_bot_config()
                await LOGGER.info(f"Registered new extension: {i}.")

        if config.bot_config["extensions"][i]:
            try:
                reload_modules(i)
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

async def resync_commands_server(guild: discord.Guild):
    await bot.tree.sync(guild=guild)

async def resync_commands():
    try:
        synced = await bot.tree.sync()
        await LOGGER.info(f"Synced {len(synced)} commands.")
    except Exception as e:
        await LOGGER.error(f"Failed to sync commands: {e}")

def reload_modules(extension_name: str):
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

    query = sql.SQL("""UPDATE {schema}.server
        SET extensions = array_remove(extensions, '{extension}')
        WHERE '{extension}' = ANY(extensions);
        """).format(
            schema = db.SCHEMA,
            extension = sql.Placeholder()
        )
    db.run(query, extension)
    if not silent:
        await interaction.response.defer()
    try:
        await bot.unload_extension(f"extensions.{extension}.main")
        reload_modules(extension)
    except:
        pass

    if not save_data:
        # remove permissions
        query = sql.SQL("SELECT name FROM {schema}.perm WHERE name LIKE '{extension}:%';").format(
            schema = db.SCHEMA,
            extension = sql.Placeholder()
        )
        permissions = db.multiple(query, extension)
        for permission in permissions:
            query = sql.SQL("DELETE FROM {schema}.permissions WHERE permission = {permission}").format(
                schema = db.SCHEMA,
                permission = sql.Placeholder()
            )
            db.run(query, permission)

            query = sql.SQL("DELETE FROM {schema}.perm WHERE name = {permission}").format(
                schema = db.SCHEMA,
                permission = sql.Placeholder()
            )
            db.run(query, permission)
        
    # remove files
        shutil.rmtree(f'{DIR}/data/{extension}', onexc=_remove_readonly)
    shutil.rmtree(f'{DIR}/extensions/{extension}', onexc=_remove_readonly)
    if not silent:
        await LOGGER.info(f":white_check_mark: Extension **{extension}** deleted.")
        await interaction.followup.send(f":white_check_mark: Extension **{extension}** deleted.")
