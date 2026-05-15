import discord, os, stat, shutil, json
from discord.ext import commands
from utils.server_config import server_config, save_server_config
from pathlib import Path
DIR = Path(__file__).resolve().parent.parent

async def uninstall(interaction: discord.Interaction, bot: commands.Bot, extension: str) -> None:
    server_config["extensions"].pop(extension)
    save_server_config()
    await interaction.response.defer()
    try:
        await bot.unload_extension(f"extensions.{extension}.main")
    except:
        pass

    # remove permissions
    with open(f"{DIR}/data/static/permissions.json", "r") as file:
        permissions: dict = json.load(file)
    permission_keys: list[str] = list(permissions.keys())
    for k in permission_keys:
        if k.startswith(extension + ":"):
            permissions.pop(k)
    with open(f"{DIR}/data/static/permissions.json", "w") as file:
        json.dump(permissions, file)
    
    # remove user fields
    with open(f"{DIR}/data/static/user.json", "r") as file:
        users: dict = json.load(file)
    user_keys: list[str] = list(users.keys())
    for k in user_keys:
        if k.startswith(extension + ":"):
            users.pop(k)
    with open(f"{DIR}/data/static/user.json", "w") as file:
        json.dump(users, file)
    
    # remove files
    shutil.rmtree(f'{DIR}/extensions/{extension}', onexc=_remove_readonly)
    shutil.rmtree(f'{DIR}/data/extensions/{extension}', onexc=_remove_readonly)

    await interaction.followup.send(f":white_check_mark: Extension **{extension}** deleted.")

def _remove_readonly(func, path, _):
    """
    Clear the read-only and hidden attributes and retry removal.
    """
    os.chmod(path, stat.S_IWRITE)
    func(path)