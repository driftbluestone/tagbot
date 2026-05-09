import json
from pathlib import Path
DIR = Path(__file__).resolve().parent
with open(f"{DIR}/../config.json", "r", encoding='utf-8') as file:
    server_config = json.load(file)

def save_server_config():
    with open(f"{DIR}/../config.json", "w", encoding="utf-8") as file:
        json.dump(server_config, file, indent=2)