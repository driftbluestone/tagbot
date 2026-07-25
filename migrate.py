import os, json
from db import db
from utils.utils import DIR

# message history
for file in os.listdir(f"{DIR}/data/history"):
    with open(f"{DIR}/data/history/{file}", "r") as f:
        data = json.load(f)
    db.insert("history", ("message", "reply"), (int(file[:-5]), data))
    os.remove(f"{DIR}/data/history/{file}")
