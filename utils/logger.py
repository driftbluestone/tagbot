import discord
from datetime import datetime
from pathlib import Path

DIR = Path(__file__).resolve().parent.parent
LOG_FILE = DIR / "data" / ".log"

_file_initialized = False
_lines: dict[int, list[str]] = {}

def _format(msg: str) -> str:
    now = datetime.now()
    return f"{now.strftime('%Y-%m-%d %H:%M:%S')}.{now.microsecond // 1000:03d} - {msg}"

def _write_file(line: str):
    global _file_initialized
    mode = "a" if _file_initialized else "w"
    _file_initialized = True
    with open(LOG_FILE, mode) as f:
        f.write(line + "\n")

async def log(msg: str, interaction: discord.Interaction | None = None):
    line = _format(msg)
    if interaction is None:
        print(line)
        _write_file(line)
    else:
        id = interaction.id
        if id not in _lines:
            _lines[id] = []
        _lines[id].append(line)
        await interaction.edit_original_response(content="\n".join(_lines[id]))
