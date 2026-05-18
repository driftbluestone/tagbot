import pathlib, os, json
DIR = pathlib.Path(__file__).resolve().parent.parent

def on_ready():
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
            
    if not os.path.isdir(f"{DIR}/data/install_logs"):
        os.mkdir(f"{DIR}/data/install_logs")
    if not os.path.isdir(f"{DIR}/data/users"):
        os.mkdir(f"{DIR}/data/users")
    if not os.path.isdir(f"{DIR}/data/history"):
        os.mkdir(f"{DIR}/data/history")
    if not os.path.isdir(f"{DIR}/data/extensions"):
        os.mkdir(f"{DIR}/data/extensions")
    if not os.path.isdir(f"{DIR}/extensions"):
        os.mkdir(f"{DIR}/extensions")