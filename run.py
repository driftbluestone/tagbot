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
    print("Module 'discord.py' not found. Installing")
    print(asyncio.run(run([sys.executable, "-m", "pip", "install", "-U", "discord.py"])))

try:
    import psutil
except ModuleNotFoundError:
    print("Module 'psutil' not found. Installing")
    print(asyncio.run(run([sys.executable, "-m", "pip", "install", "psutil"])))

vinf = sys.version_info
REQUIRED_VER = (3, 14)
VER = (vinf.major, vinf.minor)

print(f"Python version:   {vinf.major}.{vinf.minor}.{vinf.micro}")
print(f"Required version: 3.14+")
if VER < REQUIRED_VER:
    raise RuntimeError("Bot requires Python 3.14+")
import main
