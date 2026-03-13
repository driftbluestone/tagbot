import discord

async def edit_message(previous, current, channel: discord.channel):
    prev = previous.content
    cur = current.content
    embed = discord.Embed(title=f"Message edited in <#{previous.channel.id}>", description=f"**Before:** `{prev}`\n**After:** `{cur}`\n[Jump to message]({current.jump_url})")
    embed.timestamp = previous.created_at
    embed.set_footer(text=f"ID: {current.id}")
    embed.set_author(name=previous.author.name, icon_url=previous.author.avatar)
    await channel.send(embed=embed)

async def delete_message(message, channel: discord.channel):
    content = message.content
    embed = discord.Embed(title=f"Message deleted in <#{message.channel.id}>", description=f"**Content:** `{content}`")
    embed.timestamp = message.created_at
    embed.set_footer(text=f"ID: {message.id}")
    embed.set_author(name=message.author.name, icon_url=message.author.avatar)
    await channel.send(embed=embed)

async def create_delete_channel(guild_channel, channel: discord.channel.TextChannel, dialogue):
    async for entry in channel.guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_create):
        entry: discord.AuditLogEntry = entry
    creator: discord.User = entry.user

    if isinstance(guild_channel, discord.channel.CategoryChannel):
        instance = "Category"
    elif isinstance(guild_channel, discord.channel.TextChannel):
        instance = "Text Channel"
        if guild_channel.is_news():
            instance = "Announcement Channel"
    elif isinstance(guild_channel, discord.channel.VoiceChannel):
        instance = "Voice Channel"
    elif isinstance(guild_channel, discord.channel.ForumChannel):
        instance = "Forums"
    elif isinstance(guild_channel, discord.channel.StageChannel):
        instance = "Stage"

    description = f"#{guild_channel.name} {dialogue[0]}"
    if instance != "Category":
        description+=f" in category **{guild_channel.category.name}**"
    embed = discord.Embed(title=f"{dialogue[1]} {instance}", description=description)
    embed.timestamp = entry.created_at
    embed.set_author(name=creator.name, icon_url=creator.avatar)
    await channel.send(embed=embed)

async def audit_log_entry(entry: discord.AuditLogEntry):
    pass