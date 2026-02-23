import discord
async def create_message_embed(link, bot):
        link_list = link.split("/")[5:]
        channel = bot.get_channel(int(link_list[0]))
        msg = await channel.fetch_message(int(link_list[1]))
        name = msg.author.name
        pfp = msg.author.avatar
        content = msg.content
        embed=discord.Embed(description=f"{content}\n\n[Jump to message]({link})")
        embed.set_author(name=name, icon_url=pfp)
        return embed