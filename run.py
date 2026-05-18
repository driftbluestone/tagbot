import asyncio, sys, os

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
    print("Module 'discord.py' not found. Installing")
    print(asyncio.run(run([sys.executable, "-m", "pip", "install", "-U", "discord.py"])))

try:
    import psutil
except ModuleNotFoundError:
    print("Module 'psutil' not found. Installing")
    print(asyncio.run(run([sys.executable, "-m", "pip", "install", "psutil"])))

REQUIRED_VER = (3, 14, 3)
vinf = sys.version_info
import main
