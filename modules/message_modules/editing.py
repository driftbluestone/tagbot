import discord, pathlib, json, os
from modules.message_modules import message_reply
DIR = pathlib.Path(__file__).resolve().parent

async def new_edit(message: discord.Message, bot):
    id = str(message.id)
    filepath = f"{DIR}/../../data/history/{id}.json"
    if pathlib.Path(filepath).exists():
        with open(filepath, "r") as file:
            reply_id = json.load(file)
        reply: discord.Message = await message.channel.fetch_message(reply_id)
        await reply.delete()
        os.remove(filepath)
    await message_reply.message_reply(message, bot)

async def create_reply_json(id, reply_id):
    filepath = f"{DIR}/../../data/history/{reply_id}.json"
    with open(filepath, "w") as file:
        json.dump(id, file)