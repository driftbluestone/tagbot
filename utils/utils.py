import os
from utils import jsonIO
from pathlib import Path
DIR = Path(__file__).parent.parent.resolve()

if not os.path.exists(f"{DIR}/bot_info.json"):
    data = {}
    tkn = input("Paste bot token: ")
    if not tkn:
        print("No token provided.")
        quit()
    data["TOKEN"] = tkn

    print("Database setup...")
    data["DB"] = {}
    schema = input("Paste database schema name: ")
    if not schema:
        print("No database schema provided, default value `sonny` will be used.")
        schema = "sonny"
    data["DB"]["SCHEMA"] = schema
    
    host = input("Paste database host: ")
    if not host:
        print("No database host provided, default value `localhost` will be used.")
        host = "localhost"
    data["DB"]["HOST"] = host

    name = input("Paste database name: ")
    if not name:
        print("No database name provided, default value `postgres` will be used.")
        name = "postgres"
    data["DB"]["NAME"] = name

    user = input("Paste database user: ")
    if not user:
        print("No database user provided, default value `postgres` will be used.")
        user = "postgres"
    data["DB"]["USER"] = user

    passw = input("Paste database password: ")
    if not passw:
        print("No database password provided, default value `password` will be used.")
        passw = "password"
    data["DB"]["PASS"] = passw

    port = input("Paste database port: ")
    if not port:
        print("No database port provided, default value `5432` will be used.")
        port = "5432"
    data["DB"]["PORT"] = port

    jsonIO.dump(f"{DIR}/bot_info.json", data)

data = jsonIO.load(f"{DIR}/bot_info.json")