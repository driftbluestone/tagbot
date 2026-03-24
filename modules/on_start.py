import pathlib, os
DIR = pathlib.Path(__file__).resolve().parent.parent
async def on_ready():
    if not os.path.isdir(f"{DIR}/data/tags"):
        os.mkdir(f"{DIR}/data/tags")
        os.mkdir(f"{DIR}/data/tags/tags")
        os.mkdir(f"{DIR}/data/tags/users")
    if not os.path.isdir(f"{DIR}/data/history"):
        os.mkdir(f"{DIR}/data/tags/history")
    if not os.path.isdir(f"{DIR}/extensions"):
        os.mkdir(f"{DIR}/extensions")