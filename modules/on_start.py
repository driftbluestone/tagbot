import pathlib, os
from utils.utils import DIR

def on_ready():
    if not os.path.isdir(f"{DIR}/data"):
        os.mkdir(f"{DIR}/data")
    if not os.path.isdir(f"{DIR}/data/users"):
        os.mkdir(f"{DIR}/data/users")
    if not os.path.isdir(f"{DIR}/data/history"):
        os.mkdir(f"{DIR}/data/history")
    if not os.path.isdir(f"{DIR}/data/extensions"):
        os.mkdir(f"{DIR}/data/extensions")
    if not os.path.isdir(f"{DIR}/extensions"):
        os.mkdir(f"{DIR}/extensions")
    if not os.path.isdir(f"{DIR}/data/roles"):
        os.mkdir(f"{DIR}/data/roles")

on_ready()
