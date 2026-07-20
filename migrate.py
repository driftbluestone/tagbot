import os, json
from utils import db
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
    db.insert("user", ("id", "perms", "data"), (int(file[:-5]), data["permissions"], usr))
    os.remove(f"{DIR}/data/users/{file}")

# roles
for file in os.listdir(f"{DIR}/data/roles"):
    with open(f"{DIR}/data/roles/{file}", "r") as f:
        data = json.load(f)
    db.insert("role", ("id", "perms"), (int(file[:-5]), data))
    os.remove(f"{DIR}/data/roles/{file}")