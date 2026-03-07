import pathlib, os
DIR = pathlib.Path(__file__).resolve().parent
async def on_ready():
    if not os.path.isdir(f"{DIR}/../data/tags"):
        os.mkdir(f"{DIR}/../data/tags")
        os.mkdir(f"{DIR}/../data/tags/tags")
        os.mkdir(f"{DIR}/../data/tags/users")
        os.mkdir(f"{DIR}/../data/tags/history")