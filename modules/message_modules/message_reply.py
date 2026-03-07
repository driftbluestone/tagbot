import discord
from modules.message_modules import sonny, message_embed, sed

async def message_reply(message: discord.Message, bot):
    # Keep commands working
    return
    if message.content.startswith(f"{bot.command_prefix}"):
        return await bot.process_commands(message)
    # sonny react
    await sonny.sonny(message)
    # check if message contains message link
    await message_embed.check_link(message, bot)
    #sed command
    if message.content.startswith("sed/"):
        await sed.sed(message)
