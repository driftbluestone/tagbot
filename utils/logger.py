import discord, logging
from pathlib import Path

DIR = Path(__file__).parent.parent.resolve()

class Logger:
    def __init__(self, name: str = ":"):
        logging.basicConfig(
            filename=f"{DIR}/data/.log",
            level=logging.DEBUG,
            filemode='w',
            format='%(asctime)s [%(levelname)-8s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        self._logger = logging.getLogger(name)
        self.buffers = {}

    def _get_buffer(self, interaction: discord.Interaction) -> list:
        if interaction.id not in self.buffers:
            self.buffers[interaction.id] = []
        return self.buffers[interaction.id]

    async def _log_to_discord(self, msg: str, interaction: discord.Interaction) -> None:
        try:
            buffer = self._get_buffer(interaction)
            buffer.append(msg)
            content = "\n".join(buffer)
            if not interaction.response.is_done():
                await interaction.response.send_message(content)
            else:
                await interaction.edit_original_response(content=content)
        except discord.errors.NotFound:
            self._logger.warning("Interaction not found or has expired")
        except Exception as e:
            self._logger.error(f"Failed to log to Discord: {e}")

    async def _log(self, msg: str, level: int, interaction: discord.Interaction | None = None) -> None:
        self._logger.log(level, msg, stacklevel=4)
        if interaction:
            await self._log_to_discord(msg, interaction)

    async def debug(self, msg: str, i: discord.Interaction | None = None) -> None:
        await self._log(msg, logging.DEBUG, i)

    async def info(self, msg: str, i: discord.Interaction | None = None) -> None:
        await self._log(msg, logging.INFO, i)

    async def warning(self, msg: str, i: discord.Interaction | None = None) -> None:
        await self._log(msg, logging.WARNING, i)

    async def warn(self, msg: str, i: discord.Interaction | None = None) -> None:
        await self.warning(msg, i)

    async def error(self, msg: str, i: discord.Interaction | None = None) -> None:
        await self._log(msg, logging.ERROR, i)

    async def critical(self, msg: str, i: discord.Interaction | None = None) -> None:
        await self._log(msg, logging.CRITICAL, i)

    def clear_buffer(self, interaction: discord.Interaction) -> None:
        if interaction.id in self.buffers:
            del self.buffers[interaction.id]
