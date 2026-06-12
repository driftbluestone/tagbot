"""
Access internal config files.

These files are always saved in memory, so they do not need to be input as args when
calling their respective save functions.
"""
import os
from utils import jsonIO
from pathlib import Path
DIR = Path(__file__).resolve().parent.parent
__all__ = [
    "server_config", "user_config", "permissions_config",
    "save_server_config", "save_user_config", "saver_permissions_config"
    ]

if not os.path.isdir(f"{DIR}/data"):
    os.mkdir(f"{DIR}/data")
if not os.path.isdir(f"{DIR}/data/static"):
    os.mkdir(f"{DIR}/data/static")

if not os.path.exists(f"{DIR}/data/static/user.json"):
    jsonIO.dump(f"{DIR}/data/static/user.json",
                {"id": "", "permissions": {}, "roles": []})

if not os.path.exists(f"{DIR}/data/static/permissions.json"):
    jsonIO.dump(f"{DIR}/data/static/permissions.json",
                {"edit_permissions": {
                    "display_name": "Edit Permission",
                    "toggleable": False,
                    "default_enabled": False,
                    "role_assignable": True}})
    
if not os.path.exists(f"{DIR}/data/static/config.json"):
    jsonIO.dump(f"{DIR}/data/static/config.json",
                {"command_prefix": "%", "extensions": {}, "bot_admins": []})

server_config: dict = jsonIO.load(f"{DIR}/data/static/config.json")
def save_server_config():
    jsonIO.dump(f"{DIR}/data/static/config.json", server_config)

user_config: dict = jsonIO.load(f"{DIR}/data/static/user.json")
def save_user_config():
    jsonIO.dump(f"{DIR}/data/static/user.json", user_config)

permissions_config: dict = jsonIO.load(f"{DIR}/data/static/permissions.json")
def save_permisions_config():
    jsonIO.dump(f"{DIR}/data/static/permissions.json", permissions_config)