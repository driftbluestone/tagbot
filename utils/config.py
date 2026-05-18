import json, os
from pathlib import Path
DIR = Path(__file__).resolve().parent.parent

if not os.path.isdir(f"{DIR}/data"):
    os.mkdir(f"{DIR}/data")
if not os.path.isdir(f"{DIR}/data/static"):
    os.mkdir(f"{DIR}/data/static")

if not os.path.exists(f"{DIR}/data/static/user.json"):
    with open(f"{DIR}/data/static/user.json", "w") as file:
        json.dump({"id": "", "permissions": {}}, file)
if not os.path.exists(f"{DIR}/data/static/permissions.json"):
    with open(f"{DIR}/data/static/permissions.json", "w") as file:
        json.dump({"edit_permissions": "administrator"}, file)
if not os.path.exists(f"{DIR}/data/static/config.json"):
    with open(f"{DIR}/data/static/config.json", "w") as file:
        json.dump({"command_prefix": "%", "extensions": {}, "bot_admins": []}, file)

with open(f"{DIR}/data/static/config.json", "r", encoding='utf-8') as file:
    server_config = json.load(file)
def save_server_config():
    with open(f"{DIR}/data/static/config.json", "w", encoding="utf-8") as file:
        json.dump(server_config, file, indent=2)

with open(f"{DIR}/data/static/user.json", "r", encoding='utf-8') as file:
    user_config = json.load(file)
def save_user_config():
    with open(f"{DIR}/data/static/user.json", "w", encoding="utf-8") as file:
        json.dump(user_config, file, indent=2)

with open(f"{DIR}/data/static/permissions.json", "r", encoding='utf-8') as file:
    permissions_config = json.load(file)
def save_permisions_config():
    with open(f"{DIR}/data/static/permissions.json", "w", encoding="utf-8") as file:
        json.dump(permissions_config, file, indent=2)