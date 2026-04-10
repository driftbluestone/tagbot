import discord

async def edit_message(previous, current, channel: discord.PartialMessageable):
    prev = previous.content
    cur = current.content
    embed = discord.Embed(title=f"Message edited in <#{previous.channel.id}>", description=f"**Before:** `{prev}`\n**After:** `{cur}`\n[Jump to message]({current.jump_url})")
    embed.timestamp = previous.created_at
    embed.set_footer(text=f"ID: {current.id}")
    embed.set_author(name=previous.author.name, icon_url=previous.author.avatar)
    await channel.send(embed=embed)

async def delete_message(message: discord.Message, channel: discord.PartialMessageable):
    content = message.content
    async for entry in message.guild.audit_logs(limit=1, action=discord.AuditLogAction.message_delete): entry = entry
    
    embed = discord.Embed(title=f"Message deleted in <#{message.channel.id}>", description=f"**Content:** `{content}`")
    if entry.target.id == message.author.id and entry.extra.channel.id == message.channel.id:
        embed.description+=f"\nDeleted by: {entry.user.mention}"
    embed.timestamp = message.created_at
    embed.set_footer(text=f"ID: {message.id}")
    embed.set_author(name=message.author.name, icon_url=message.author.avatar)
    await channel.send(embed=embed)

async def audit_log_entry(entry: discord.AuditLogEntry, channel: discord.PartialMessageable):
    category: str = entry.category.name

    if category != "delete":
        mention: str = entry.target.mention
    else:
        mention = entry.before.name

    action: str = entry.action.name
    component = action.split("_")[0]
    if component == "overwrite": component = "channel overwrite in"

    embed = discord.Embed()
    embed.set_author(name = entry.user.name, icon_url = entry.user.avatar)

    if category == "create":
        embed.description = f"Created new {component} {mention}\n"
    elif category == "update":
        embed.description = f"Updated {component} {mention}\n"
        await generate_update_table(embed, entry.before, "**Before:**\n")
        await generate_update_table(embed, entry.after, "**After:**\n")
    elif category == "delete":
        embed.description = f"Deleted {component} '{mention}'\n"

    await channel.send(embed=embed)

async def generate_update_table(embed: discord.Embed, entry, when):
    embed.description += when
    for attribute, value in entry.__dict__.items():
        if value is None: 
            continue
        elif isinstance(value, discord.Permissions):
            embed.description += f"{attribute.title()}: "
            permissions = []
            for perm, enabled in value:
                if enabled: permissions.append(perm.title())
            permissions = str(permissions)[1:-1].replace("'", "`")
            embed.description += f"{permissions}\n"
        else:
            embed.description+=f"{attribute.title()}: {value}\n"
