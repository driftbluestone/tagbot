import pathlib, os
DIR = pathlib.Path(__file__).resolve().parent.parent

def on_ready():
    if not os.path.isdir(f"{DIR}/data"):
        os.mkdir(f"{DIR}/data")
    if not os.path.isdir(f"{DIR}/data/install_logs"):
        os.mkdir(f"{DIR}/data/install_logs")
    if not os.path.isdir(f"{DIR}/data/users"):
        os.mkdir(f"{DIR}/data/users")
    if not os.path.isdir(f"{DIR}/data/history"):
        os.mkdir(f"{DIR}/data/history")
    if not os.path.isdir(f"{DIR}/data/extensions"):
        os.mkdir(f"{DIR}/data/extensions")
    if not os.path.isdir(f"{DIR}/extensions"):
        os.mkdir(f"{DIR}/extensions")