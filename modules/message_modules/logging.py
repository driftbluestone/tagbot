import discord

async def edit_message(previous, current, channel):
    if channel == 0: return
    prev = previous.content
    cur = current.content
    embed = discord.Embed(title=f"Message edited in <#{previous.channel.id}>", description=f"**Before:** `{prev}`\n**After:** `{cur}`\n[Jump to message]({current.jump_url})")
    embed.timestamp = previous.created_at
    embed.set_footer(text=f"ID: {current.id}")
    embed.set_author(name=previous.author.name, icon_url=previous.author.avatar)
    await channel.send(embed=embed)

async def delete_message(message, channel):
    if channel == 0: return
    content = message.content
    embed = discord.Embed(title=f"Message deleted in <#{message.channel.id}>", description=f"**Content:** `{content}`")
    embed.timestamp = message.created_at
    embed.set_footer(text=f"ID: {message.id}")
    embed.set_author(name=message.author.name, icon_url=message.author.avatar)
    await channel.send(embed=embed)