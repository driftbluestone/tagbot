import discord, os, asyncio, importlib, sys, shutil, typing
from discord import app_commands
from discord.ext import commands
from functools import cache
from psycopg import sql
from utils import jsonIO, logger
from utils.utils import DIR, bot, bot_config
from db import db, server, users
from api import gui
LOGGER = logger.Logger()

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Extensions(bot=bot))
    try:
        synced = await bot.tree.sync()
        await LOGGER.info(f"Synced {len(synced)} commands.")
    except Exception as e:
        await LOGGER.error(f"Error syncing commands: {e}")
    for extension in server.extensions(0).keys():
        await bot.load_extension(f"extensions.{extension}.main")
    await load()

class Extensions(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    extension = app_commands.Group(name="extension", description="Manage extensions")

    @extension.command(name="toggle", description="Toggle extensions")
    async def extension_toggle(self, interaction: discord.Interaction):
        if not users.check_permission(interaction.guild.id, interaction.user.id, "manage_extensions"):
            return await interaction.response.send_message(":warning: No permission.", ephemeral=True)
        return await interaction.response.send_message(view=ExtensionManager(interaction.guild))

    @extension.command(name="add", description="Requires bot admin. Install extensions")
    async def extension_add(self, interaction: discord.Interaction, repo: str):
        if interaction.user.id in bot_config["bot_admins"]:
            return await interaction.response.send_message(":warning: No permission.", ephemeral=True)
        if not repo.startswith("https://github.com/"):
            return await interaction.response.send_message(f":warning: Please specify a git repo", ephemeral=True)
        
        repo_name = repo.split("/")[-1]
        if server.check_extension(0, repo_name):
            return await interaction.response.send_message(":warning: Extension already installed.")
        await install_repo(interaction, repo, repo_name)
        await init_extension(repo_name)
    
    @extension.command(name="update", description="Requires bot admin. Update extensions")
    async def extension_update(self, interaction: discord.Interaction, repo: str):
        if interaction.user.id in bot_config["bot_admins"]:
            return await interaction.response.send_message(":warning: No permission.", ephemeral=True)
        if not repo.startswith("https://github.com/"):
            return await interaction.response.send_message(f":warning: Please specify a git repo", ephemeral=True)
        
        repo_name = repo.split("/")[-1]
        if server.check_extension(0, repo_name):
            await uninstall(interaction, repo_name, True, True)
            interaction = None
        await install_repo(interaction, repo, repo_name)
        await init_extension(repo_name)

    @extension.command(name="delete", description="Requires bot admin. Uninstall extensions")
    async def extension_delete(self, interaction: discord.Interaction, extension: str, save_data: typing.Optional[bool] = True):
        if interaction.user.id in bot_config["bot_admins"]:
            return await interaction.response.send_message(":warning: No permission.", ephemeral=True)
        if not server.check_extension(0, extension):
            return await interaction.response.send_message(":warning: Extension not found.", ephemeral=True)
        await uninstall(interaction, extension, save_data)

class ExtensionManager(gui.PageUI):
    """Manage which extensions are enabled or disabled via /extension toggle"""
    def __init__(self, guild: discord.Guild, page = 1):
        self.extensions = server.extensions(guild.id)
        extensions = list(self.extensions.keys())
        super().__init__(element_count = len(extensions), page = page, data_transfer=guild)
        extensions = extensions[((self.page-1)*10):(self.page*10)]

        for extension in extensions:
            buttonstyle = discord.ButtonStyle.success if self.extensions[extension] else discord.ButtonStyle.danger
            button = discord.ui.Button(label=extension, style=buttonstyle, custom_id=extension)
            button.callback = self.button_callback
            self.add_item(button)

    async def button_callback(self, interaction: discord.Interaction):
        if not users.check_permission(interaction.guild.id, interaction.user.id, "manage_extensions"):
            return await interaction.response.send_message(":warning: No permission.", ephemeral=True)
        extension = interaction.data["custom_id"]
        self.extensions[extension] = not self.extensions[extension]

        # sync slash commands
        if self.extensions[extension]:
            db.insert("extensions", ("server_id", "extension"), (), (interaction.guild.id, extension))
            await sync(extension, interaction.guild)
            
        else:
            db.delete("extensions", ("server_id", "extension"), (interaction.guild.id, extension))
            await unsync(extension, interaction.guild)
            
        view = ExtensionManager(self.data_transfer, self.page)
        await interaction.response.defer(ephemeral=True, thinking=False)
        await interaction.message.edit(view=view)

# internal extension installation functions
async def install_repo(interaction: discord.Interaction, repo: str, repo_name: str):
    await LOGGER.info(f"Downloading {repo_name} from {repo}...", interaction)
    await subprocess(["git", "clone", repo, f"{DIR}/extensions/{repo_name}"])

    dependencies = f"{DIR}/extensions/{repo_name}/dependencies.json"
    if os.path.exists(dependencies):
        await LOGGER.info(f"Downloaded {repo_name} from {repo}.", interaction)
        await LOGGER.info("Found dependencies. Installing...", interaction)
        dependencies = jsonIO.load(interaction, dependencies)
        await install_dependencies(interaction, dependencies)
        await LOGGER.info("Dependencies installed.", interaction)
    else:
        await LOGGER.info(f"Installed {repo_name} from {repo}.", interaction)
    
async def install_dependencies(interaction: discord.Interaction, dependencies: dict):
    if "pip" in dependencies:
        for package in dependencies["pip"]:
            await LOGGER.info(f"pip dependency {package} found. Installing...", interaction)
            await subprocess([sys.executable, "-m", "pip", "install", package])
            await LOGGER.info(f"pip dependency {package} Installed.", interaction)

    if "extension" in dependencies:
        for extension in dependencies["extension"]:
            extension_name = extension.split("/")[-1]
            await LOGGER.info(f"Extension dependency {extension_name} found. Installing...", interaction)
            await install_repo(interaction, extension, extension_name)
            await LOGGER.info(f"Extension dependency {extension_name} Installed.", interaction)

    if "other" in dependencies:
        for other in dependencies["other"]:
            await LOGGER.warn(f"Other dependency '{other}' requires manual installation.", interaction)

async def subprocess(args):
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

async def init_extension(extension: str):
    try:
        os.mkdir(f"{DIR}/extensions/{extension}")
    except FileExistsError:
        pass
    if os.path.exists(f"{DIR}/extensions/{extension}/init.py"):
        importlib.import_module(f"extensions.{extension}.init")
    await bot.load_extension(f"extensions.{extension}.main")
    await LOGGER.info(f"Initialized new extension: {extension}.")

@cache
async def get_extension_commands(extension):
    extension_commands = []
    for cog in bot.cogs.values():
        if cog.__module__.split["."][1] == extension:
            extension_commands.extend[cog.get_app_commands()]

async def sync(extension: str, guild: discord.Guild):
    for command in get_extension_commands(extension):
        bot.tree.add_command(command, guild=guild)
    await bot.tree.sync(guild=guild)

async def unsync(extension: str, guild: discord.Guild):
    for command in get_extension_commands(extension):
        bot.tree.remove_command(command, guild=guild)
    await bot.tree.sync(guild=guild)

async def load():
    extensions = db.multiple(f"SELECT * FROM {db.SCHEMA}.extensions WHERE server_id != 0")
    for server_id, extension in extensions:
        await sync(server_id, extension)

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
    
    if not silent:
        await interaction.response.defer()
    try:
        await bot.unload_extension(f"extensions.{extension}.main")
        unload_modules(extension)
        ids = db.multiple(f"SELECT server_id FROM {db.SCHEMA}.extensions WHERE server_id != 0 and extension = {extension}")
        for server_id, in ids:
            await unsync(extension, discord.Object(id=server_id))
    except:
        pass

    # remove files
    if not save_data:
        delete_data(extension)
        shutil.rmtree(f'{DIR}/data/{extension}', onexc=_remove_readonly)
    shutil.rmtree(f'{DIR}/extensions/{extension}', onexc=_remove_readonly)

    if not silent:
        await LOGGER.info(f":white_check_mark: Extension **{extension}** deleted.")
        await interaction.followup.send(f":white_check_mark: Extension **{extension}** deleted.")

def delete_data(extension):
    # drop all tables created by extension
    query = sql.SQL("""SELECT TABLENAME FROM pg_catalog.pg_tables
                    WHERE schemaname = {schema}
                    AND tablename LIKE '{extension}$%';
                    """).format(
        schema = db.SCHEMA,
        extension = sql.Placeholder()
        )
    tables = db.multiple(query, extension)
    for table, in tables:
        query = sql.SQL("DROP TABLE {schema}.{table};").format(
            schema = db.SCHEMA,
            table = sql.Identifier(table)
        )
        db.run(query)

    # remove from extension table
    query = sql.SQL("DELETE FROM {schema}.extensions WHERE extension = {extension};").format(
        schema = db.SCHEMA,
        extension = sql.Placeholder()
    )
    db.run(query, extension)

    # remove permissions
    query = sql.SQL("SELECT name FROM {schema}.perm WHERE name LIKE '{extension}:%';").format(
        schema = db.SCHEMA,
        extension = sql.Placeholder()
    )
    permissions = db.multiple(query, extension)
    for permission, in permissions:
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
    