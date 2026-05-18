import sys, asyncio
from pathlib import Path
DIR = Path(__file__).resolve().parent.parent

async def run(args):
    try:
        result = await asyncio.create_subprocess_exec(
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT
        )
        stdout, _ = await result.communicate()
        return stdout.decode()
    except Exception as e:
        return str(e)
    
try:
    import PyInstaller
except ModuleNotFoundError:
    print("Module 'pyinstaller' not found. Installing")
    print(asyncio.run(run([sys.executable, "-m", "pip", "install", "pyinstaller"])))

bundle = [sys.executable, "-m", "PyInstaller", "--onefile",
                 "--add-data", f"{DIR}/api;api",
                 "--add-data", f"{DIR}/cogs;cogs",
                 "--add-data", f"{DIR}/data/static;data/static",
                 "--add-data", f"{DIR}/modules;modules",
                 "--add-data", f"{DIR}/utils;utils",
                 "--add-data", f"{DIR}/config.json;data/static/",
                 "--add-data", f"{DIR}/main.py;.",
                 "run.py"]

print(asyncio.run(run(bundle)))