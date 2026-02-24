import json, pathlib
DIR = pathlib.Path(__file__).resolve().parent
with open(f"{DIR}/../config.json", "r") as file:
    server_config = json.load(file)

async def save_server_config():
    with open(f"{DIR}/../config.json", "w") as file:
        json.dump(server_config, file)