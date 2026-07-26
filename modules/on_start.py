import os
from db import db
from utils.utils import DIR, data

SCHEMA = data["DB"]["SCHEMA"]

def on_ready():
    if not os.path.isdir(f"{DIR}/data"):
        os.mkdir(f"{DIR}/data")
    if not os.path.isdir(f"{DIR}/data/extensions"):
        os.mkdir(f"{DIR}/data/extensions")
    if not os.path.isdir(f"{DIR}/extensions"):
        os.mkdir(f"{DIR}/extensions")
    db._init()

on_ready()
