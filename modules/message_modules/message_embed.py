import discord, re
async def check_link(message, bot):
    if re.search("https:\/\/discord\.com\/channels\/\d+\/\d+\/\d+", message.content):
        link = re.search("https:\/\/discord\.com\/channels\/\d+\/\d+\/\d+", message.content)
        link = link.group()
        embed =  await create_message_embed(link, bot)
        if embed == None: return
        await message.reply(embed=embed)
        
async def create_message_embed(link, bot):
    link_list = link.split("/")[5:]
    channel = bot.get_channel(int(link_list[0]))
    if channel == None: return
    msg: discord.Message = await channel.fetch_message(int(link_list[1]))

    name = msg.author.name
    pfp = msg.author.avatar
    content = msg.content

    embed=discord.Embed(description=f"{content}\n\n[Jump to message]({link})", timestamp=msg.created_at)
    for i in msg.attachments:
        embed.set_image(url=i)
    for i in msg.embeds:
        if i.url.startswith("https://tenor"): continue
        embed.set_image(url=i.url)
    embed.set_author(name=name, icon_url=pfp)
    
    embed.set_footer(text=f"From #{msg.channel.name}")
    return embed