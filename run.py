import asyncio, sys

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
    import discord
except ModuleNotFoundError:
    print("Module 'discord.py' not found. Would you like to install?")
    if input("Enter 'y' to install: ").lower() == 'y':
        print(asyncio.run(run([sys.executable, "-m", "pip", "install", "-U", "discord.py"])))
    else:
        print("Installation skipped.")
        quit()

try:
    import psutil
except ModuleNotFoundError:
    print("Module 'psutil' not found. Would you like to install?")
    if input("Enter 'y' to install: ").lower() == 'y':
        print(asyncio.run(run([sys.executable, "-m", "pip", "install", "psutil"])))
    else:
        print("Installation skipped.")
        quit()

try:
    import orjson
except ModuleNotFoundError:
    print("Module 'orjson' not found. Would you like to install?")
    if input("Enter 'y' to install: ").lower() == 'y':
        print(asyncio.run(run([sys.executable, "-m", "pip", "install", "orjson"])))
    else:
        print("Installation skipped.")
        quit()

try:
    import psycopg2
except ModuleNotFoundError:
    print("Module 'psycopg2' not found. Would you like to install?")
    if input("Enter 'y' to install: ").lower() == 'y':
        print(asyncio.run(run([sys.executable, "-m", "pip", "install", "psycopg2.binary"])))
    else:
        print("Installation skipped.")
        quit()

vinf = sys.version_info
REQUIRED_VER = (3, 14)
VER = (vinf.major, vinf.minor)

if VER < REQUIRED_VER:
    print(f"Python version: {vinf.major}.{vinf.minor}.{vinf.micro}")
    raise RuntimeError("Bot requires Python 3.14+")
import main