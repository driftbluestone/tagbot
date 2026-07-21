"""
Access internal config files.

These files are always held in memory, so they do not need to be input as args when
calling their respective save functions.
"""
import os
from utils import jsonIO
from utils.utils import DIR
__all__ = [
    "server_config", "user_config", "permissions_config",
    "save_server_config", "save_user_config", "saver_permissions_config"
    ]

if not os.path.isdir(f"{DIR}/data"):
    os.mkdir(f"{DIR}/data")

if not os.path.exists(f"{DIR}/data/user.json"):
    jsonIO.dump(f"{DIR}/data/user.json",
                {"id": "", "permissions": {}, "roles": []})

if not os.path.exists(f"{DIR}/data/permissions.json"):
    jsonIO.dump(f"{DIR}/data/permissions.json",
                {"edit_permissions": {
                    "display_name": "Edit Permission",
                    "toggleable": False,
                    "default_enabled": False,
                    "role_assignable": True}})

if not os.path.exists(f"{DIR}/data/config.json"):
    jsonIO.dump(f"{DIR}/data/config.json",
                {"command_prefix": "%", "extensions": {}, "bot_admins": []})

server_config: dict = jsonIO.load(f"{DIR}/data/config.json")
def save_server_config():
    jsonIO.dump(f"{DIR}/data/config.json", server_config)

user_config: dict = jsonIO.load(f"{DIR}/data/user.json")
def save_user_config():
    jsonIO.dump(f"{DIR}/data/user.json", user_config)

permissions_config: dict = jsonIO.load(f"{DIR}/data/permissions.json")
def save_permisions_config():
    jsonIO.dump(f"{DIR}/data/permissions.json", permissions_config)
