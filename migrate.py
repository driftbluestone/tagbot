import os, json
from utils import db, jsonIO
from utils.bot import bot
from utils.utils import DIR

# message history
for file in os.listdir(f"{DIR}/data/history"):
    with open(f"{DIR}/data/history/{file}", "r") as f:
        data = json.load(f)
    db.insert("history", ("message", "reply"), (int(file[:-5]), data))
    os.remove(f"{DIR}/data/history/{file}")

# user files
for file in os.listdir(f"{DIR}/data/users"):
    with open(f"{DIR}/data/users/{file}", "r") as f:
        data = json.load(f)
    usr = data.copy()
    usr.pop("id")
    usr.pop("permissions")
    db.insert("user_perms", ("server_id", "user_id"), ("perms",), (bot.guilds[0].id, data["id"], data["permissions"]), )
    db.insert("user_data", ("user_id",), ("data",), (jsonIO.dumps(usr),))
    os.remove(f"{DIR}/data/users/{file}")

# roles
for file in os.listdir(f"{DIR}/data/roles"):
    with open(f"{DIR}/data/roles/{file}", "r") as f:
        data = json.load(f)
    db.insert("role", ("server_id","role_id"), ("perms",), (bot.guilds[0].id, int(file[:-5]), jsonIO.dumps(data)))
    os.remove(f"{DIR}/data/roles/{file}")