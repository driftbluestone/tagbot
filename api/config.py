import os
from utils import jsonIO
from api import _ext as ext
from typing import Any
from pathlib import Path
DIR = Path(__file__).resolve().parent.parent

def create_field(name: str, data: type|Any) -> bool:
    """
    Define a new field for storing data in the extension config file.
    data must be (of) a json compatible type.
    """
    extension = ext()
    path = Path(f"{DIR}/data/extensions/{extension}")
    if not os.path.exists(path):
        os.mkdir(path)
    path /= "config.json"
    if not os.path.isfile(path):
        jsonIO.dump(path, {})
    config = jsonIO.load(path)
    
    def _register(name: str, data: type|Any) -> bool:
        if name not in config:
            config[name] = data() if isinstance(data, type) else data 
            return True
        return False
    
    if not _register(name, data):
        return False
    jsonIO.dump(path, config)
    return True

def get(namespace: str = None) -> dict:
    """
    Get extension config data
    """
    if namespace is None:
        namespace = ext()
    data = jsonIO.load(f"{DIR}/data/extensions/{namespace}/config.json")
    return data

def set(field: str, data):
    """
    Set config data and save it to disk.
    Will raise a KeyError if the field is not in the config
    """
    extension = ext()
    cfg = jsonIO.load(f"{DIR}/data/extensions/{extension}/config.json")
    if field not in cfg:
        raise KeyError
    cfg[field] = data
    jsonIO.dump(f"{DIR}/data/extensions/{extension}/config.json", cfg)

def overwrite(data: dict) -> None:
    """
    Overwrite all config data
    """
    extension = ext()
    jsonIO.dump(f"{DIR}/data/extensions/{extension}/config.json", data)

def datadir() -> Path:
    """
    Get the direct path to the /data/extension/name folder
    """
    extension = ext()
    return Path(f"{DIR}/data/extensions/{extension}")