import re, discord
from modules.tags import users

async def sed(message):
    user = users.get_user_profile(message.author.id)
    if not user["permissions"]["use_sed"]: return
    if message.reference is None:
        replied_message = None
        message_history = [message async for message in message.channel.history(limit=25)]
        s_content = message.content.split('/')
        pattern = s_content[1]
        for i in message_history:
            match = re.search(pattern, i.content, flags=re.IGNORECASE)
            if i.content.startswith("sed/"):
                pass
            elif match:
                replied_message = i
                break
    else:
        replied_message = await message.channel.fetch_message(message.reference.message_id)
    if replied_message:        
        await process_sed(message, replied_message)
    else:
        await message.add_reaction("❌")

async def process_sed(message, replied_message):
    reply_content = replied_message.content
    s_content = message.content.split('/', 3)
    
    pattern = s_content[1]

    if replied_message.author.bot:
        await message.add_reaction("❌")
        return

    if len(s_content) > 2:
        replace = s_content[2]
    else:
        replace = ""
    count = 1
    if len(s_content) > 3 and s_content[3] == "g":
        count = 0
    if not pattern:
        await message.add_reaction("❌")
    else:
        sub = re.sub(pattern, replace, reply_content, count, flags=re.IGNORECASE)
        
        embed = discord.Embed(description=sub, color=0x222222)
        embed.set_author(name=replied_message.author, icon_url=replied_message.author.avatar.url)
        embed.set_footer(text = f"sed replace in #{message.channel}")
        await message.reply(embed=embed)