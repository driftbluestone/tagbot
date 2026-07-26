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

    @extension.command(name="add", description="Requires bot admin. Install extensions")
    async def extension_add(self, interaction: discord.Interaction, repo: str):
        if interaction.user.id in config.bot_config["bot_admins"]:
            return await interaction.response.send_message(":warning: No permission.", ephemeral=True)
        if not repo.startswith("https://github.com/"):
            return await interaction.response.send_message(f":warning: Please specify a git repo", ephemeral=True)
        repo_name = repo.split("/")[-1]
        if server.check_extension(0, repo_name):
            return await interaction.response.send_message(":warning: Extension already installed.")
        await _install_repo(interaction, repo, repo_name)
    
    @extension.command(name="update", description="Requires bot admin. Update extensions")
    async def extension_update(self, interaction: discord.Interaction, repo: str):
        if interaction.user.id in config.bot_config["bot_admins"]:
            return await interaction.response.send_message(":warning: No permission.", ephemeral=True)
        if not repo.startswith("https://github.com/"):
            return await interaction.response.send_message(f":warning: Please specify a git repo", ephemeral=True)
        repo_name = repo.split("/")[-1]
        if server.check_extension(0, repo_name):
            pass
        else:
            await _install_repo(interaction, repo, repo_name)

    @extension.command(name="delete", description="Requires bot admin. Uninstall extensions")
    async def extension_delete(self, interaction: discord.Interaction, extension: str, save_data: typing.Optional[bool] = True):
        if interaction.user.id in config.bot_config["bot_admins"]:
            return await interaction.response.send_message(":warning: No permission.", ephemeral=True)
        if extension not in config.bot_config["extensions"].keys():
            return await interaction.response.send_message(":warning: Extension not found.", ephemeral=True)
        await uninstall(interaction, extension, save_data)

# internal extension installation functions
async def _install_repo(interaction: discord.Interaction, repo: str, repo_name: str):
    await LOGGER.info(f"Downloading {repo_name} from {repo}...", interaction)
    await _subprocess(["git", "clone", repo, f"{DIR}/extensions/{repo_name}"])
    dependencies = f"{DIR}/extensions/{repo_name}/dependencies.json"
    if os.path.exists(dependencies):
        await LOGGER.info(f"Downloaded {repo_name} from {repo}.", interaction)
        await LOGGER.info("Found dependencies. Installing...", interaction)
        dependencies = jsonIO.load(interaction, dependencies)
        await _install_dependencies(interaction, dependencies)
        await LOGGER.info("Dependencies installed.", interaction)
    else:
        await LOGGER.info(f"Installed {repo_name} from {repo}.", interaction)
    

async def _install_dependencies(interaction: discord.Interaction, dependencies: dict):
    if "pip" in dependencies:
        for package in dependencies["pip"]:
            await LOGGER.info(f"pip dependency {package} found. Installing...", interaction)
            await _subprocess([sys.executable, "-m", "pip", "install", package])
            await LOGGER.info(f"pip dependency {package} Installed.", interaction)
    if "extension" in dependencies:
        for extension in dependencies["extension"]:
            extension_name = extension.split("/")[-1]
            await LOGGER.info(f"Extension dependency {extension_name} found. Installing...", interaction)
            await _install_repo(interaction, extension, extension_name)
            await LOGGER.info(f"Extension dependency {extension_name} Installed.", interaction)
    if "other" in dependencies:
        for other in dependencies["other"]:
            await LOGGER.warn(f"Other dependency '{other}' requires manual installation.", interaction)

async def _subprocess(args):
    try:
        result = await asyncio.create_subprocess_exec(
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT
        )
        stdout, _ = await result.communicate()
        await LOGGER.info(stdout.decode())
    except Exception as e:
        await LOGGER.warning(str(e))

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
            unload_modules(extension)
            await bot.load_extension(f"extensions.{extension}.main")
        else:
            await bot.unload_extension(f"extensions.{extension}.main")
        await resync_commands()

        await LOGGER.info(f"Extension '{extension}' {state}.")

async def load_extensions():
    extensions, = db.get("server", (0,), ("server_id",), ("extensions",),)
    await resync_commands()

async def init_extension(extension: str):
    query = sql.SQL("SELECT {extension} = ANY(extensions) FROM {schema}.server WHERE server_id = 0").format(
        schema = db.SCHEMA,
        extension = sql.Identifier(extension)
    )
    exists, = db.single(query)
    if not exists:
        try:
            os.mkdir(f"{DIR}/extensions/{extension}")
        except FileExistsError:
            pass
        if os.path.exists(f"{DIR}/extensions/{extension}/init.py"):
            importlib.import_module(f"extensions.{extension}.init")
        await bot.load_extension(f"extensions.{extension}.main")
        await LOGGER.info(f"Initialized new extension: {extension}.")
    # else:
    #     try:
    #         unload_modules(extension)
    #         await bot.load_extension(f"extensions.{extension}.main")
    #         await LOGGER.info(f"Initialized extension: {extension}.")
    #     except Exception as e:
    #         await LOGGER.error(f"Failed to initialize extension {extension}: {e}")
    
async def resync_commands_server(guild: discord.Guild):
    await bot.tree.sync(guild=guild)

async def resync_commands():
    try:
        synced = await bot.tree.sync()
        await LOGGER.info(f"Synced {len(synced)} commands.")
    except Exception as e:
        await LOGGER.error(f"Failed to sync commands: {e}")

def unload_modules(extension_name: str):
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
        SET extensions = array_remove(extensions, {extension})
        WHERE {extension} = ANY(extensions);
        """).format(
            schema = db.SCHEMA,
            extension = sql.Placeholder()
        )
    db.run(query, extension)
    if not silent:
        await interaction.response.defer()
    try:
        await bot.unload_extension(f"extensions.{extension}.main")
        unload_modules(extension)
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
