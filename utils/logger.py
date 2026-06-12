"""
Log things, create a new instance of the `Logger` class in order to use
"""

import discord
import logging
from typing import Optional
import inspect
from pathlib import Path
DIR = Path(__file__).resolve().parent.parent
__all__ = ["Logger"]

class Logger:
    def __init__(self):
        logging.basicConfig(
            filename=f"{DIR}/data/.log",
            level=logging.DEBUG,
            filemode='w'
        )
        self.logger = logging.getLogger(":")
        self.buffers = {}

    def _get_buffer(self, interaction: Optional[discord.Interaction]) -> list:
        if not interaction:
            return None
        if interaction.id not in self.buffers:
            self.buffers[interaction.id] = []
        return self.buffers[interaction.id]

    async def _log_to_discord(self, msg: str, interaction: Optional[discord.Interaction] = None) -> None:
        if not interaction:
            return
        try:
            buffer = self._get_buffer(interaction)
            buffer.append(msg)
            content = "\n".join(buffer)
            await interaction.edit_original_response(content=content)
        except discord.errors.NotFound:
            self.logger.warning("Interaction not found or has expired")
        except Exception as e:
            self.logger.error(f"Failed to log to Discord: {e}")

    async def _log(self, msg: str, level: int, interaction: Optional[discord.Interaction] = None ) -> None:
        self.logger.log(level, msg, stacklevel=5)
        if interaction:
            await self._log_to_discord(msg, interaction)

    async def debug(self, msg: str, i: Optional[discord.Interaction] = None) -> None:
        await self._log(msg, logging.DEBUG, i)

    async def info(self, msg: str, i: Optional[discord.Interaction] = None) -> None:
        await self._log(msg, logging.INFO, i)

    async def warning(self, msg: str, i: Optional[discord.Interaction] = None) -> None:
        await self._log(msg, logging.WARNING, i)

    async def warn(self, msg: str, i: Optional[discord.Interaction] = None) -> None:
        await self.warning(msg, i)

    async def error(self, msg: str, i: Optional[discord.Interaction] = None) -> None:
        await self._log(msg, logging.ERROR, i)

    async def critical(self, msg: str, i: Optional[discord.Interaction] = None) -> None:
        await self._log(msg, logging.CRITICAL, i)

    def clear_buffer(self, interaction: discord.Interaction) -> None:
        if interaction.id in self.buffers:
            del self.buffers[interaction.id]
