from discord.ext import commands
from psycopg import sql
from db import db

class Cog(commands.Cog):
    async def cog_check(self, ctx: commands.Context):
        self.qualified_name
        extension = self.__module__.split(".")[1]
        query = sql.SQL("""SELECT * FROM {schema}.server
                        WHERE {extension} = ANY(extensions)
                        AND server_id = {server_id}
                        """).format(
            schema = db.SCHEMA,
            extension = sql.Placeholder(),
            server_id = sql.Placeholder()
            )
        db.single(query, (extension, ctx.guild.id))

