import os, json
from utils import db
from utils.utils import DIR

for file in os.listdir(f"{DIR}/data/history"):
    with open(f"{DIR}/data/history/{file}", "r") as f:
        data = json.load(f)
    db.run("INSERT INTO sonny.history (message, reply) VALUES (%s, %s);", (int(file[:-5]), data))