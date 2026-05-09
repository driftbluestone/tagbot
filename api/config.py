import json, os
from api import _ext as ext
from typing import Any
from pathlib import Path
DIR = Path(__file__).resolve().parent.parent

def create_field(name: str | list[str], data: type|Any | list[type|Any]) -> bool:
    """
    Define a new field for storing data in the extension config file.
    data must be (of) a json compatible type.
    To register multiple data fields at once, both name and data must be lists, and must be equal in length
    """
    extension = ext()
    path = Path(f"{DIR}/data/extensions/{extension}")
    if not os.path.exists(path):
        os.mkdir(path)
    path /= "config.json"
    if not os.path.isfile(path):
        with open(path, "w") as file:
            json.dump({}, file)
    with open(path, "r") as file:
            config: dict = json.load(file)
    
    def _register(name: str, data: type|Any) -> bool:
        if name not in config:
            config[name] = data() if isinstance(data, type) else data 
            return True
        return False
    
    if isinstance(name, list):
        for nm, dt in zip(name, data, strict=True):
            if not _register(nm, dt): return False
    else:
        if not _register(name, data): return False
    with open(path, "w") as file:
        json.dump(config, file, indent=2)
    return True

def get(namespace: str = None) -> dict:
    """
    Get extension config data
    """
    if namespace is None:
        namespace = ext()
    with open(f"{DIR}/data/extensions/{namespace}/config.json", "r") as file:
        data: dict = json.load(file)
    return data

def set(field: str, data):
    """
    Set config data and save it to disk.
    Will raise a KeyError if the field is not in the config
    """
    extension = ext()
    with open(f"{DIR}/data/extensions/{extension}/config.json", "r") as file:
        cfg = json.load(file)
    if field not in cfg:
        raise KeyError
    cfg[field] = data
    with open(f"{DIR}/data/extensions/{extension}/config.json", "w") as file:
        json.dump(cfg, file, indent=2)


def overwrite(data: dict) -> None:
    """
    Overwrite all config data
    """
    extension = ext()
    with open(f"{DIR}/data/extensions/{extension}/config.json", "w") as file:
        json.dump(data, file, indent=2)