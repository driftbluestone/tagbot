import discord, os, asyncio, importlib, json
from discord import app_commands
from discord.ext import commands
from modules import uninstall_extension
from modules.bot import bot
from api import gui
from utils.server_config import server_config, save_server_config

from pathlib import Path
DIR = Path(__file__).resolve().parent.parent

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Extensions(bot=bot))
    await load_extensions(bot)

class Extensions(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    extension = app_commands.Group(name="extension", description="Magage Extenions")
    
    @extension.command(name="toggle", description = "Toggle extensions")
    async def extension_toggle(self, interaction: discord.Interaction):
        if not interaction.user.id in server_config["bot_admins"]:
            return await interaction.response.send_message(":warning: No permission.", ephemeral=True)
        view = ExtensionManager(interaction, bot)
        return await interaction.response.send_message(view=view)
    
    @extension.command(name="add", description = "Install extensions")
    async def extension_add(self, interaction: discord.Interaction, repo: str):
        if not interaction.user.id in server_config["bot_admins"]:
            return await interaction.response.send_message(":warning: No permission.", ephemeral=True)
        if not repo.startswith("https://github.com/"):
            return await interaction.response.send_message(f":warning: Please specify a git repo", ephemeral=True)
        
        repo_name = repo.split("/")[-1]
        if os.path.isdir(f"{DIR}/../extensions/{repo_name}"):
            return await interaction.response.send_message("Extension already installed.")
        os.mkdir(f"{DIR}/extensions/{repo_name}")
        output = await Installer(interaction, repo).install_extension()
        await load_extensions(bot)
        return await interaction.response.send_message(content=f"Sucessfully added module {repo_name}!\n{output}")
    
    @extension.command(name="delete", description = "Uninstall extensions")
    async def extension_delete(self, interaction: discord.Interaction, extension: str):
        if not interaction.user.id in server_config["bot_admins"]:
            return await interaction.response.send_message(":warning: No permission.", ephemeral=True)
        if extension not in server_config["extensions"].keys():
            return await interaction.response.send_message(":warning: Extension not found.", ephemeral=True)
        uninstall_extension.uninstall(interaction, bot, extension)

class Installer:
    def __init__(self, interaction: discord.Interaction, repo: str):
        self.extension = repo.split("/")[-1]
        self.repo = repo
        self.ext = self.extension
        self.interaction = interaction
        self.output: list = [f"Installing {self.extension} from {repo}...\n"]
        self.output_full = self.output
        
    async def subprocess(self, args: list) -> str:
        try:
            result = await asyncio.create_subprocess_exec(
                *args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT
            )
            stdout, _ = await asyncio.wait_for(result.communicate())
            output = stdout.decode()
        except Exception as e:
            output = str(e)
        return output
    
    async def install_extension(self):
        msg = f"Extension dependency {self.extension} found. Installing..."
        self.output.append(msg)
        self.output_full.append(msg)
        await self.interaction.edit_original_response("\n".join(self.output))

        args = ["git", "clone", self.repo, f"{DIR}/extensions/{self.extension}"]
        msg = await self.subprocess(args)
        self.output_full.append(msg)
        
        msg = f"Extension dependency {self.extension} found. Installed."
        self.output[-1] = msg
        self.output_full.append(msg)
        await self.interaction.edit_original_response("\n".join(self.output))
        
        await self.dependencies()
    
    async def dependencies(self):
        filepath = f"{DIR}/extensions/{self.extension}/dependencies.json"
        filepath = f"{DIR}/dependencies.json"
        if not os.path.exists(filepath):
            return await self.interaction.edit_original_response("\n".join(self.output))
        
        with open(filepath, "r") as file:
            requirements = json.load(file)
        if "pip" in requirements:
            for pip in requirements["pip"]:
                await self.install_pip(pip)
            self.output = self.output[:-len(requirements["pip"])]
        if "extension" in requirements:
            for extension in requirements["extension"]:
                self.extension = extension
                await self.install_extension()
            self.output = self.output[:-len(requirements["extension"])]
        if "other" in requirements:
            for other in requirements["other"]:
                msg = f"Other dependency {other} found. Manual installation required."
                self.output.append(msg)
                self.output_full.append(msg)
            await self.interaction.edit_original_response("\n".join(self.output))

        msg = [f"Installed {self.ext} from {self.repo}."]
        self.output[0] = msg
        self.output_full.append(msg)
        await self.interaction.edit_original_response("\n".join(self.output))
        with open(f"{DIR}/data/logs/{self.ext}.txt", "w") as file:
            file.write(self.output_full)
    
    async def install_pip(self, pip: str):
        msg = f"Pip dependency {pip} found. Installing..."
        self.output.append(msg)
        self.output_full.append(msg)
        await self.interaction.edit_original_response("\n".join(self.output))

        args = ['python3', '-m', 'pip', 'install', pip]
        msg = await self.subprocess(args)
        self.output_full.append(msg)

        msg = f"Pip dependency {pip} found. Installed."
        self.output[-1] = msg
        self.output_full.append(msg)
        await self.interaction.edit_original_response("\n".join(self.output))

class ExtensionManager(gui.MenuGUI):
    """Manage which extensions are enabled or disabled via /extension toggle"""
    def __init__(self, interaction, page = 1):
        super().__init__(interaction=interaction, element_count=len(server_config["extensions"].keys()), page=page)
        extensions = list(server_config["extensions"].keys())
        extensions = extensions[((self.page-1)*10):(self.page*10)]
        for extension in extensions:
            buttonstyle = discord.ButtonStyle.danger
            if server_config["extensions"][extension]: buttonstyle = discord.ButtonStyle.success
            button = discord.ui.Button(label = extension, style=buttonstyle, custom_id=extension)
            button.callback = self.open_modal_button_callback
            self.add_item(button)

    async def open_modal_button_callback(self, interaction: discord.Interaction):
        if not interaction.user.id in server_config["bot_admins"]:
            return await interaction.response.send_message(":warning: No permission." ,ephemeral=True)
        extension = interaction.data["custom_id"]
        server_config["extensions"][extension] = not server_config["extensions"][extension]
        view = ExtensionManager(self.interaction, bot, self.page)
        await self.interaction.edit_original_response(view=view)
        await load_extensions(bot)
        await interaction.response.defer(ephemeral=True, thinking=False)

async def load_extensions(bot: commands.Bot):
    for i in os.listdir(f"{DIR}/extensions"):
        if i not in server_config["extensions"]:
            server_config["extensions"][i] = True
            
            os.mkdir(f"{DIR}/data/extensions/{i}")
            if os.path.exists(f"{DIR}/extensions/{i}/init.py"):
                importlib.import_module(f"extensions.{i}.init")
            save_server_config()
        if server_config["extensions"][i]:
            try: await bot.load_extension(f"extensions.{i}.main")
            except Exception as e: raise e 
        else:
            try: await bot.unload_extension(f"extensions.{i}.main")
            except: pass
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} commands.")
    except Exception as exception:
        print(f"Error syncing commands: {exception}")
