import discord
from modules import message_embed
from db import db

async def new_edit(message: discord.Message, deleted = False):
    id = message.id
    result = db.get("history", (id,), ("message",), ("reply",))
    if result is None:
        return
    _, reply_id = result
    reply: discord.PartialMessage = message.channel.get_partial_message(reply_id)
    await reply.delete()
    db.delete("history", ("message",), (id,))
    if not deleted:
        await message_embed.message_reply(message)

async def create_reply_entry(id: int, reply_id: int):
    db.insert("history", ("message",), ("reply",), (reply_id, id))
