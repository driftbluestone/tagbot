import os, json
from psycopg import sql
from db import db
from utils.utils import DIR

server_id = 1428076898000568492
if server_id == 0:
    raise Exception("SET SERVER ID")

# message history
for file in os.listdir(f"{DIR}/data/history"):
    with open(f"{DIR}/data/history/{file}", "r") as f:
        data = json.load(f)
    db.insert("history", ("message",), ("reply",), (int(file[:-5]), data))
    os.remove(f"{DIR}/data/history/{file}")

db.run(f"CREATE TABLE IF NOT EXISTS {db.SCHEMA.as_string()}.sonny_tags$tags (" + ", ".join(["name TEXT PRIMARY KEY",
                  "owner BIGINT",
                  "type TEXT",
                  "content TEXT",
                  "aliases TEXT[] DEFAULT NULL",
                  "args TEXT[] DEFAULT NULL"
                ]) + ")")

for file in os.listdir(f"{DIR}/data/extensions/sonny_tags/tags"):
    if not file.endswith(".json"):
        continue
    with open(f"{DIR}/data/extensions/sonny_tags/tags/{file}", "r") as f:
        data = json.load(f)
    content = ""

    type = data["type"]
    if type == "code":
        type = f"code:{data["lang"]}"
        with open(f"{DIR}/data/extensions/sonny_tags/tags/{file[:-5]}.{data["lang"]}", "r") as f:
            content = f.read()
        os.remove(f"{DIR}/data/extensions/sonny_tags/tags/{file[:-5]}.{data["lang"]}")

    if "args" in data:
        args = data["args"]
    else:
        args = []

    if type == "alias":
        content = data["alias_of"]
        aliases = []
    else:
        aliases = data["aliases"]

    if type == "message":
        content = data["message_link"]

    if type == "plaintext":
        with open(f"{DIR}/data/extensions/sonny_tags/tags/{file[:-5]}.txt", "r") as f:
            content = f.read()
        os.remove(f"{DIR}/data/extensions/sonny_tags/tags/{file[:-5]}.txt")
    
    db.insert("sonny_tags$tags", ("name",), ("owner", "type", "content", "aliases", "args"), (file[:-5], int(data["owner"]), type, content, aliases, args))

    os.remove(f"{DIR}/data/extensions/sonny_tags/tags/{file}")

db.run(f"CREATE TABLE IF NOT EXISTS {db.SCHEMA.as_string()}.sonny_tags$users (user_id BIGINT PRIMARY KEY, tags TEXT[], space INT)")

def tag_size(name):
    # get size of tag
    query = sql.SQL("""SELECT pg_column_size(t)
        AS total_row_bytes
        FROM {schema}.sonny_tags$tags AS t
        WHERE name::text = {name};""").format(
            schema = db.SCHEMA,
            name = sql.Placeholder()
        )
    size, = db.single(query, (name,))
    return size

for file in os.listdir(f"{DIR}/data/users"):
    with open(f"{DIR}/data/users/{file}", "r") as f:
        data = json.load(f)

    for permission, value in data["permissions"].items():
        if value is None:
            continue
        db.insert("permissions", ("server_id", "id", "permission"), ("value",), (server_id, int(data["id"]), permission, value))
    size = sum([tag_size(name) for name in data["sonny_tags:tags"]])
    db.insert("sonny_tags$users", ("user_id",), ("tags", "space"), (int(data["id"]), data["sonny_tags:tags"], size))

    os.remove(f"{DIR}/data/users/{file}")

for extension in os.listdir(f"{DIR}/data/extensions"):
    db.insert("extensions", ("server_id", "extension"), (), (0, extension))