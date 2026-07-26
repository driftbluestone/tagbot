import discord, functools
from discord.ext import commands
from discord.utils import MISSING
from typing import Callable
from db import server
from commands import *

def _get_server_id(*args) -> int:
    for arg in args:
        if isinstance(arg, discord.Guild):
            return arg.id
        elif hasattr(arg, "guild") and arg.guild:
            return arg.guild.id

class Cog(commands.Cog):
    async def cog_check(self, ctx: commands.Context):
        """Do not override this function, use `command_check()` instead"""
        if not self.command_check(ctx):
            return False
        extension = self.__module__.split(".")[1]
        return server.check_extension(ctx.guild.id, extension)

    async def command_check(self, ctx) -> bool:
        """Docstring copied from discord.py. Copyright (c) 2015-present Rapptz

        A special method that registers as a :func:`~discord.ext.commands.check`
        for every command and subcommand in this cog.
    
        This function **can** be a coroutine and must take a sole parameter,
        ``ctx``, to represent the :class:`.Context`.
        """
        return True
    
    @classmethod
    def listener(cls, name: str = MISSING):
        extension = cls.__module__.split(".")[1]
        def decorator(func: Callable):
            @functools.wraps(func)
            async def wrapper(self, *args, **kwargs):
                server_id = _get_server_id(*args)
                if not server.check_extension(server_id, extension):
                    return
                return await func(self, *args, **kwargs)
            return super(Cog, cls).listener(name)(wrapper)
        return decorator
