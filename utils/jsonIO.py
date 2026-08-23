"""
Util module for writing / reading json with orjson

Functions prefixed with `a` are asyncronous and run on a seperate thread,

Functions suffixed with `s` or `b` input / return string or bytes, respectively
"""
import orjson, asyncio
from pathlib import Path
from orjson import JSONDecodeError
__all__ = [
    "read", "load", "write", "dump",
    "dumps", "dumpb", "loads", "loadb",
    "aread", "aload", "awrite", "adump"
    ]

def read(path: str | Path) -> object:
    with open(path, "rb") as file:
        return orjson.loads(file.read())

def load(path: str | Path) -> object:
    with open(path, "rb") as file:
        return orjson.loads(file.read())

def write(path: str | Path, data) -> None:
    with open(path, "wb") as file:
        file.write(orjson.dumps(data, option=orjson.OPT_INDENT_2))

def dump(path: str | Path, data) -> None:
    with open(path, "wb") as file:
        file.write(orjson.dumps(data, option=orjson.OPT_INDENT_2))

def dumps(data) -> str:
    return orjson.dumps(data).decode()

def dumpb(data) -> bytes:
    return orjson.dumps(data)

def loads(data: str) -> object:
    return orjson.loads(data.encode())

def loadb(data: bytes) -> object:
    return orjson.loads(data)

async def aread(path: str | Path) -> object:
    return await asyncio.to_thread(read, path)

async def aload(path: str | Path) -> object:
    return await asyncio.to_thread(load, path)

async def awrite(path: str | Path, data) -> None:
    return await asyncio.to_thread(write, path, data)

async def adump(path: str | Path, data) -> None:
    return await asyncio.to_thread(dump, path, data)