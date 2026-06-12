"""
Util module for writing / reading json files with orjson

Automatically handles context
"""
import orjson
from pathlib import Path

def read(path: str | Path) -> object:
    with open(path, "rb", encoding="utf-8") as file:
        return orjson.loads(file.read())

def load(path: str | Path) -> object:
    with open(path, "rb", encoding="utf-8") as file:
        return orjson.loads(file.read())

def write(path: str | Path, data) -> None:
    with open(path, "wb", encoding="utf-8") as file:
        file.write(orjson.dumps(data))

def dump(path: str | Path, data) -> None:
    with open(path, "wb", encoding="utf-8") as file:
        file.write(orjson.dumps(data))

def dumps(data) -> str:
    return orjson.dumps(data).decode()

def dumpb(data) -> bytes:
    return orjson.dumps(data)

def loads(data: str) -> object:
    return orjson.loads(data.encode())

def loadb(data: bytes) -> object:
    return orjson.dumps(data)