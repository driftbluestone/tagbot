import discord, pathlib, json, os
from utils import message_embed
DIR = pathlib.Path(__file__).resolve().parent.parent

async def new_edit(message: discord.Message, deleted = False):
    id = str(message.id)
    filepath = f"{DIR}/data/history/{id}.json"
    if pathlib.Path(filepath).exists():
        with open(filepath, "r") as file:
            reply_id = json.load(file)
        reply: discord.PartialMessage = message.channel.get_partial_message(reply_id)
        await reply.delete()
        os.remove(filepath)
    if not deleted: await message_embed.message_reply(message)

async def create_reply_json(id, reply_id):
    filepath = f"{DIR}/data/history/{reply_id}.json"
    with open(filepath, "w") as file:
        json.dump(id, file)
