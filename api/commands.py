import discord, functools
from discord.ext import commands
from discord.utils import MISSING
from typing import Callable
from psycopg import sql
from db import db

def _extension_enabled(extension: str, server_id: int) -> bool:
    query = sql.SQL("""SELECT * FROM {schema}.server
                            WHERE {extension} = ANY(extensions)
                            AND server_id = {server_id}
                            """).format(
                schema = db.SCHEMA,
                extension = sql.Placeholder(),
                server_id = sql.Placeholder()
                )
    value, = db.single(query, (extension, server_id))
    return value

def _get_server_id(*args) -> int:
    for arg in args:
        if isinstance(arg, discord.Guild):
            return arg.id
        elif hasattr(arg, "guild") and arg.guild:
            return arg.guild.id

class Cog(commands.Cog):
    async def cog_check(self, ctx: commands.Context):
        extension = self.__module__.split(".")[1]
        return _extension_enabled(extension, ctx.guild.id)
    
    @classmethod
    def listener(cls, name: str = MISSING):
        extension = cls.__module__.split(".")[1]
        def decorator(func: Callable):
            @functools.wraps(func)
            async def wrapper(self, *args, **kwargs):
                server_id = _get_server_id(*args)
                if not _extension_enabled(extension, server_id):
                    return
                return await func(self, *args, **kwargs)
            return super(Cog, cls).listener(name)(wrapper)
        return decorator
