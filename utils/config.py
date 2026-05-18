import json
from pathlib import Path
DIR = Path(__file__).resolve().parent.parent

with open(f"{DIR}/config.json", "r", encoding='utf-8') as file:
    server_config = json.load(file)
def save_server_config():
    with open(f"{DIR}/config.json", "w", encoding="utf-8") as file:
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