import discord, os
from json import dump, load
from pathlib import Path
from discord.ext import commands
bot = commands.Bot(command_prefix="%",
    allowed_mentions=discord.AllowedMentions(
        users=False,
        everyone=False,
        roles=False,
        replied_user=True,
    ),
    intents=discord.Intents.all())

tags, admins, users = {}, {}, {}
DIR = Path(__file__).parent.absolute()
with open(f"{DIR}/TOKEN.txt", "r") as file:
    TOKEN = file.read()
if not os.path.isdir(f"{DIR}/tags"):
    os.mkdir(f"{DIR}/tags")
    os.mkdir(f"{DIR}/tags/global_tags")
    with open(f"{DIR}/tags/global_tags/tags.json", "w") as file:
        dump({}, file)
    with open(f"{DIR}/tags/global_tags/admins.json", "w") as file:
        dump([True, []], file)
    with open(f"{DIR}/tags/global_tags/users.json", "w") as file:
        dump({}, file)
for filepath in os.listdir(f"{DIR}/tags"):
    with open(f"{DIR}/tags/{filepath}/tags.json", "r") as file:
        tags[filepath] = load(file)
    with open(f"{DIR}/tags/{filepath}/admins.json", "r") as file:
        admins[filepath] = load(file)
    with open(f"{DIR}/tags/{filepath}/users.json", "r") as file:
        users[filepath] = load(file)

unique_tags=["add","edit","delete","admin","alias","list","owner","meta"]
chars = ['1','2','3','4','5','6','7','8','9','0',
         'a','b','c','d','e','f','g','h','i','j',
         'k','l','m','n','o','p','q','r','s','t',
         'u','v','w','x','y','z','_','-']
@bot.event
async def on_ready():
    print(f'Tagging it up as {bot.user}!')

@bot.command(name="t")
async def t(ctx, tag: str=None, *args):
    await get_tag(ctx, tag, args)
@bot.command(name="tag")
async def tag(ctx, tag: str=None, *args):
    await get_tag(ctx, tag, args)

async def get_tag(ctx, tag, args):
    print(ctx.message.content)
    print(tags)
    print(users)
    if tag == None:
        return await ctx.reply(f":information_source: %t `add|edit|delete|admin|alias|list|owner|meta`")
    
    if tag in unique_tags:
        return await unique_tag(ctx, tag, args, ctx.message.content)
    tag_type = await get_tag_type(ctx, tag)
    if tag_type == False:
        return await ctx.reply(f":warning: Tag {tag} doesn't exist.")
    if tag_type == "global_tags" and tag.startswith("*"):
        tag = tag[1:]
    if tags[tag_type][tag][2]:
        tag = tags[tag_type][tag][1]
        if tag.startswith("*"):
            tag_type = "global_tags"
            tag = tag[1:]
    with open(f"{DIR}/tags/{tag_type}/{tag}.txt", "r") as file:
        body = file.read()
    return await ctx.reply(body)

async def check_permission(ctx, tag_type):
    if admins[tag_type][0] and not tag_type == "global_tags":
        return False
    if str(ctx.author.id) in admins[tag_type][1] or (ctx.author.guild_permissions.administrator and not tag_type == "global_tags"):
        return False
    return True

async def dump_tag(ctx, cont, name, tag_type):
    body = cont[(8+len(name)):]
    with open(f"{DIR}/tags/{tag_type}/{name}.txt", "w") as file:
        file.write(body)

async def generate_files(server_id):
    if not os.path.isdir(f"{DIR}/tags/{server_id}"):
        os.mkdir(f"{DIR}/tags/{server_id}")
        with open(f"{DIR}/tags/{server_id}/admins.json", "x") as file:
            dump([False, []], file)
        with open(f"{DIR}/tags/{server_id}/users.json", "x") as file:
            dump({}, file)
        with open(f"{DIR}/tags/{server_id}/tags.json", "w") as file:
            dump({}, file)
        admins[server_id] = [True, []]
        users[server_id] = {}
        tags[server_id] = {}

async def generate_metadata(tag_type, tag, user_id, alias):
    if alias == "":
        tag_meta = [user_id, [], False]
    else:
        tag_meta = [user_id, alias, True]
    tags[tag_type][tag] = tag_meta
    with open(f"{DIR}/tags/{tag_type}/tags.json", "w") as file:
        dump(tags[tag_type], file)
    users[tag_type][user_id] = users[tag_type].get(user_id, [])
    users[tag_type][user_id].append(tag)
    users[tag_type][user_id].sort()
    with open(f"{DIR}/tags/{tag_type}/users.json", "w") as file:
        dump(users[tag_type], file)

async def get_tag_type(ctx, name):
    server_id = str(ctx.guild.id)
    if name.startswith("*") and name[1:] in tags["global_tags"]:
        return "global_tags"
    elif name in tags[server_id]:
        return server_id
    elif name in tags["global_tags"]:
        return "global_tags"
    else:
        return False

async def unique_tag(ctx, tag, args, cont):
    if tag == "add":
        return await add_tag(ctx, args, cont)
    elif tag == "edit":
        return await edit_tag(ctx, args, cont)
    elif tag == "delete":
        return await delete_tag(ctx, args, True)
    elif tag == "admin":
        return await admin_function(ctx, args)
    elif tag == "alias":
        return await alias_tag(ctx, args)
    elif tag == "list":
        return await list_tag(ctx, args)
    elif tag == "owner":
        return await owner_tag(ctx, args[0], await tag_owner(args[0], await get_tag_type(ctx, args[0])), ":information_source:")
    
async def admin_function(ctx, args):
    user_id = str(ctx.author.id)
    server_id = str(ctx.guild.id)
    await generate_files(server_id)
    if user_id not in admins[server_id][1] and not ctx.author.guild_permissions.administrator:
        return await ctx.reply(":warning: No permission.")
    if args == ():
        return await ctx.reply(":information_source: %t admin `delete|promote|limit`")
    tag = args[0]
    if tag == "delete":
        return await delete_tag(ctx, args, False)
    elif tag == "promote":
        return await admin_promote(ctx, args[1:])
    elif tag == "limit":
        return await limit_to_admins(ctx)
    else:
        return await ctx.reply(":warning: Invalid admin tag.")

async def add_tag(ctx, args, cont):
    server_id = str(ctx.guild.id)
    if args == ():
        if await check_permission(ctx, server_id):
            return await ctx.reply(":warning: No permission.")
        return await ctx.reply(":information_source: %t add `name` `body`")

    user_id = str(ctx.author.id)
    name = str(args[0]).lower()
    tag_type = server_id
    if name.startswith("*"):
        tag_type = "global_tags"
        name=name[1:]
    await generate_files(server_id)
    if await check_permission(ctx, tag_type):
        return await ctx.reply(":warning: No permission.")
    if any(char not in chars for char in name):
        return await ctx.reply(f":warning: Tag name must consist of characters a-z, 0-9, _, or -. ")

    if name in unique_tags:
        return await ctx.reply(f":warning: Tag {name} already exists.")
    tags[tag_type] = tags.get(tag_type, {})
    if name in tags["global_tags"]:
        return await ctx.reply(f":warning: Tag **{name}** already exists, and is owned by <@{tags["global_tags"][name][0]}>.")
    if (not tag_type == "global_tags") and (name in tags[server_id]):
        return await ctx.reply(f":warning: Tag **{name}** already exists, and is owned by <@{tags[server_id][name][0]}>.")
    
    await generate_metadata(tag_type, name, user_id, "")
    await dump_tag(ctx, cont, name, tag_type)

    return await ctx.reply(f"✅ Added tag {name}!")

async def edit_tag(ctx, args, cont):
    if args == ():
        return await ctx.reply(":information_source: %t edit `name` `new_body`")
    user_id = str(ctx.author.id)
    name = str(args[0])
    tag_type = await get_tag_type(ctx, name)
    owner = await tag_owner(args[0], tag_type)
    if owner != user_id:
        return await owner_tag(ctx, name, owner, ":warning:")
    await dump_tag(ctx, cont, name, tag_type, False)
    return await ctx.reply(f"✅ Edited tag {name}.")

async def delete_tag(ctx, args, check_ownership):
    if args == ():
        return await ctx.reply(":information_source: %t delete `tag`")
    user_id = str(ctx.author.id)
    tag = args[0]
    tag_type = await get_tag_type(ctx, tag)
    owner = await tag_owner(tag, tag_type)
    if check_ownership and owner != user_id:
        return await owner_tag(ctx, tag, owner, ":warning:")
    aliased = ""
    if tags[tag_type][tag][2]:
        tags[tag_type][tags[tag_type][tag][1]][1].remove(tag)
        tags[tag_type].pop(tag)
        users[tag_type][user_id].remove(tag)
    else:
        for i in tags[tag_type][tag][1]:
            users[tag_type][tags[tag_type][i][0]].remove(i)
            tags[tag_type].pop(i)
            aliased = "and surrounding aliases "
        tags[tag_type].pop(tag)
        users[tag_type][user_id].remove(tag)
        os.remove(f"{DIR}/tags/{tag_type}/{tag}.txt")
        with open(f"{DIR}/tags/{tag_type}/tags.json", "w") as file:
            dump(tags[tag_type], file)
        with open(f"{DIR}/tags/{tag_type}/users.json", "w") as file:
            dump(users[tag_type], file)
    return await ctx.reply(f"✅ Tag **{tag}** {aliased}deleted.")

async def admin_promote(ctx, args):
    server_id = str(ctx.guild.id)
    if args == ():
        descbuilder = ""
        x=1
        for i in admins[server_id][1]:
            descbuilder += f"{x}. <@{i}>"
        if len(descbuilder) >= 3900:
            with open(f"{DIR}/message.txt", "w") as file:
                file.write(descbuilder)
                return await ctx.reply(f":information_source: %t admin promote `@user|username`\nAdmins:", file=file)
        reply = ""
        if descbuilder != "":
            reply = "Admins:\n"
        return await ctx.reply(f":information_source: %t admin promote `@user|username`\n{reply}{descbuilder}")

    user = args[0]
    promote_type = str(ctx.guild.id)
    if user.startswith("*"):
        if await check_permission(ctx, "global_tags"):
            return await ctx.reply(f":warning: You cannot promote a user to global admin.")
        promote_type = "global_tags"
        user = user[1:]
    if user.startswith("<@"):
        user = user[2:-1]
    else:
        user = str(ctx.guild.get_member_named(user).id)

    if user in admins[promote_type][1]:
        admins[promote_type][1].remove(user)
        with open(f"{DIR}/tags/{server_id}/admins.json", "w") as file:
            dump(admins[promote_type], file)
        return await ctx.reply(f"✅ Removed user <@{user}>.")
    else:
        admins[promote_type][1].append(user)
        with open(f"{DIR}/tags/{server_id}/admins.json", "w") as file:
            dump(admins[promote_type], file)
        return await ctx.reply(f"✅ Added role <@{user}>.")

async def limit_to_admins(ctx):
    server_id = str(ctx.guild.id)
    await generate_files(server_id)
    if admins[server_id][0]:
        admins[server_id][0] = False
        return await ctx.reply("✅ Only admins can now create tags.")
    else:
        admins[server_id][0] = True
        return await ctx.reply("✅ Any user can now create tags.")

async def alias_tag(ctx, args):
    server_id = str(ctx.guild.id)
    if args == ():
        if await check_permission(ctx, server_id):
            return await ctx.reply(":warning: No permission.")
        return await ctx.reply(":information_source: %t alias `new tag` `other tag`")
    
    user_id = str(ctx.author.id)
    new_tag = str(args[0]).lower()
    new_tag_type = server_id
    if new_tag.startswith("*"):
        new_tag_type = "global_tags"
        new_tag = new_tag[1:]
    if await check_permission(ctx, new_tag_type):
        return await ctx.reply(":warning: No permission.")
    if new_tag in tags[new_tag_type]:
        return await ctx.reply(f":warning: Tag **{new_tag}** already exists.")
    try:
        old_tag = args[1]
    except:
        return await ctx.reply(":warning: Please select a tag to alias to.")
    old_tag_type = server_id
    if old_tag.startswith("*"):
        old_tag_type = "global_tags"
        old_tag[1:]
    if new_tag_type == "global_tags" and not old_tag_type == "global_tags":
        return await ctx.reply(":warning: Cannot alias global tag to local tag.")
    
    if any(char not in chars for char in new_tag):
        return await ctx.reply(f":warning: Tag name must consist of characters a-z, 0-9, _, or -. ")

    if not old_tag in tags[old_tag_type]:
        return await ctx.reply(f":warning: Tag **{old_tag}** doesn't exist.")
    
    await generate_files(server_id)
    await generate_metadata(new_tag_type, new_tag, user_id, old_tag)
    tags[old_tag_type][old_tag][1].append(new_tag)
    return await ctx.reply(f"✅ Aliased **{new_tag}** to **{old_tag}**.")

async def list_tag(ctx, args):
    server_id = str(ctx.guild.id)
    if args == ():
        user = str(ctx.author.id)
    else:
        user = str(args[0])
        if user.startswith("<@"):
            user = user[2:-1]
        else:
            user = str(ctx.guild.get_member_named(user).id)
    descbuilder = ""
    num = 1
    try:
        for i in users["global_tags"][user]:
            descbuilder += f"{num}. *{i}\n"
            num+=1
    except: pass
    try:
        for i in users[server_id][user]:
            descbuilder += f"{num}. {i}\n"
            num+=1
    except: pass
    if len(descbuilder) >= 3900:
        with open(f"{DIR}/message.txt", "w") as file:
            file.write(descbuilder)
            return await ctx.reply(f":information_source: <@{user}> has the following tags:", file=file)
    if descbuilder == "":
        return await ctx.reply(f":information_source: <@{user}> has no tags.")
    return await ctx.reply(f":information_source: <@{user}> has the following tags:\n{descbuilder}")

async def tag_owner(tag, tag_type):
    if tag in unique_tags:
        return "unique"
    if tag_type == False:
        return False
    return tags[tag_type][tag][0]

async def owner_tag(ctx, tag, owner, msg):
    if owner == "unique":
        return await ctx.reply(f"{msg} Tag **{tag}** is a unique tag.")
    elif owner == False:
        return await ctx.reply(f"{msg} Tag **{tag}** doesn't exist.")
    return await ctx.reply(f"{msg} Tag **{tag}** is owned by <@{owner}>.")

bot.run(TOKEN)
