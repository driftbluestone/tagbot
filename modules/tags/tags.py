import discord, subprocess, uuid, pathlib, json, re, os, Levenshtein, heapq
from modules import config
from modules.tags import users
from modules.message_modules import message_embed
from modules.tags.tag_utils import get_tag_data, check_creation_permission
DIR = pathlib.Path(__file__).resolve().parent
SPECIAL_TAGS = ["add", "edit", "delete", "alias", "list", "owner", "search", "admin", "raw"]
DISPLAYED_SPECIAL_TAGS = ["add", "edit", "delete", "alias", "list", "owner", "search"]
ADMIN_TAGS = ["delete", "promote", "limit", "ban"]
VALID_NAME_CHARS = set("0123456789abcdefghijklmnopqrstuvwxyz_-")

async def context_formatter(ctx, bot):
    message = ctx.message.content
    message = message.split(" ")
    if len(message) != 1:
        tag = message[1].lower()
        message = message[2:]
    else:
        tag = None
    await get_tag(ctx, bot, tag, message)

async def get_tag(ctx, bot, tag, message):
    if tag == None:
        return await ctx.reply(f":information_source: %t `{"|".join(DISPLAYED_SPECIAL_TAGS)}`")
    tag.lower()
    if tag in SPECIAL_TAGS:
        return await special_tag(ctx, tag, message)
    data, filepath = await get_tag_data(ctx, tag, True, False)
    if data == False:
        match =  await search_tag(ctx, tag, 1)
        return await ctx.reply(f"Tag **{tag}** not found, did you mean {match}?")
    if data["type"] == "message":
        link = data["message_link"]
        embed = await message_embed.create_message_embed(link, bot)
        return await ctx.reply(embed=embed)
    elif data["type"] == "code":
        return await container(ctx, tag, message)
    elif data["type"] == "plaintext":
        with open(f"{filepath[:-5]}.txt", "r", encoding="utf-8") as file:
            content = file.read()
        return await ctx.reply(content)
    elif data["type"] == "alias":
        await get_tag(ctx, bot, data["alias_of"], message)

async def special_tag(ctx, tag, message):
    if message == []:
        message = ["", ""]
    message[0].lower

    if tag == "add":
        await add_tag(ctx, message[0], message[1:])
    elif tag == "edit":
        await edit_tag(ctx, message[0], message[1:])
    elif tag == "delete":
        await delete_tag(ctx, message[0])
    elif tag == "alias":
        await alias_tag(ctx, message[0], message[1])
    elif tag == "list":
        await list_tag(ctx, message[0])
    elif tag == "owner":
        await owner_tag(ctx, message[0])
    elif tag == "search":
        out = await search_tag(ctx, message[0], 5)
        await ctx.reply(f":information_source: {out}")
    elif tag == "raw":
        await raw_tag(ctx, message[0])
    elif tag == "admin":
        return await admin_tag(ctx, message[0], message[1:])

async def admin_tag(ctx, tag, args):
    if not await users.permission_check(ctx.author, "tag_admin"): return await ctx.reply(":warning: No permission.")
    if tag == "": return await ctx.reply(f":information_source: %t admin `{"|".join(ADMIN_TAGS)}`")

    if args == []:
        args = ["", ""]
    elif len(args) == 1:
        args = [args[0], ""]

    if tag == "delete":
        await delete_tag(ctx, args[0], True)
    elif tag == "promote":
        await promote_user(ctx, args[0])
    elif tag == "limit":
        await limit_creation(ctx)
    elif tag == "ban":
        await ban_user(ctx, args[0], args[1])

async def promote_user(ctx, user):
    if user == "": return await ctx.reply(":information_source: %t admin promote `user`")
    user = await users.resolve_user(ctx, user)
    if not user: return await ctx.reply(":warning: Couldn't find user.")
    msg = ":white_check_mark: Sucessfully "
    if user["permissions"]["tag_admin"]:
        msg += "demoted"
        user["permissions"]["tag_admin"] = False
    else:
        msg += "promoted"
        user["permissions"]["tag_admin"] = True
    users.save_user_profile(user)
    return await ctx.reply(f"{msg} <@{user["id"]}>.")

async def limit_creation(ctx):
    msg = ":white_check_mark: "
    if config.server_config["limit_tags_to_admins"]:
        msg += "Only admins"
        config.server_config["limit_tags_to_admins"] = False
    else:
        msg += "Any user"
        config.server_config["limit_tags_to_admins"] = True
    await config.save_server_config()
    return await ctx.reply(f"{msg} can now create tags.")

async def ban_user(ctx, user, type):
    if (user == "") or (type == "") or (type not in ["add", "view", "sed"]): return await ctx.reply(":information_source: %t admin ban `user` `add|view|sed`")
    user = await users.resolve_user(ctx, user)
    if not user: return await ctx.reply(":warning: Couldn't find user.")
    user = users.get_user_profile(user["id"])
    if type == "add":
        type = "create_tags"
    elif type == "view":
        type = "view_tags"
    elif type == "sed":
        type = "use_sed"
    ban = ""
    if user["permissions"][type]:
        user["permissions"][type] = False
    else:
        ban = "un"
        user["permissions"][type] = True
    users.save_user_profile(user)
    return await ctx.reply(f":white_check_mark: <@{user["id"]}> {ban}banned.")

async def add_tag(ctx, tag_name, tag_body, success_text = "Created"):
    can_create = await check_creation_permission(ctx)
    if not can_create: return
    if tag_name == "": return await ctx.reply(":information_source: %t add `name` `body`")

    tag_body = " ".join(tag_body)
    tag_name = tag_name.lower()
    filepath =f"{DIR}/../../data/tags/tags/{tag_name}.json"
    if pathlib.Path(filepath).exists():
        with open(filepath, "r") as file:
            data = json.load(file)
        return await ctx.reply(f":warning: Tag **{tag_name}** already exists and is owned by <@{data["owner"]}>.")
    if any(char not in VALID_NAME_CHARS for char in tag_name):
        return await ctx.reply(f":warning: Tag name must consist of characters a-z, 0-9, _, or -. ")
    await create_tag(ctx, tag_name, tag_body, filepath, success_text)

async def edit_tag(ctx, tag, content):
    if tag == "": return await ctx.reply(":information_source: %t edit `name` `new body`")

    data, filepath = await get_tag_data(ctx, tag, True, True)
    if data == False:
        return await ctx.reply(f":warning: Tag **{tag}** not found.")
    
    if data["type"] == "code":
        os.remove(f"{filepath[:-5]}.py")
    if data["type"] == "plaintext":
        os.remove(f"{filepath[:-5]}.txt")
    
    await create_tag(ctx, tag, " ".join(content), filepath, "Edited")

async def delete_tag(ctx, tag, override = False, silent = False):
    if tag == "": return await ctx.reply(":information_source: %t delete `tag`")

    data, filepath = await get_tag_data(ctx, tag, True, not override)
    if data == False: return await ctx.reply(f":warning: Tag **{tag}** does not exist.")
    # make sure all aliases are deleted
    deleted_aliases = ""
    if data["type"] != "alias":
        aliases = data["aliases"]
        for alias in aliases:
            deleted_aliases = " and surrounding aliases"
            await delete_tag(ctx, alias, True, True)
    else:
        alias_of, alias_filepath = await get_tag_data(ctx, data["alias_of"], True, False)
        alias_of["aliases"].remove(tag)
        with open(alias_filepath, "w") as file:
            json.dump(alias_of, file)
    if data["type"] == "code":
        os.remove(f"{filepath[:-5]}.py")
    if data["type"] == "plaintext":
        os.remove(f"{filepath[:-5]}.txt")
    os.remove(filepath)

    user = users.get_user_profile(data["owner"])
    user["tags"].remove(tag)
    users.save_user_profile(user)

    if not silent: return await ctx.reply(f":white_check_mark: Tag **{tag}**{deleted_aliases} deleted.")

async def alias_tag(ctx, new_tag, tag):
    can_create = await check_creation_permission(ctx)
    if not can_create: return
    if new_tag == "": return await ctx.reply(":information_source: %t alias `new` `existing`")
    if tag == "": return await ctx.reply(":warning: Please provide a tag to alias to.")

    data, filepath = await get_tag_data(ctx, tag, True, False)
    if data == False: return await ctx.reply(f":warning: Tag **{tag}** does not exist.")
    if data["type"] == "alias":
        return await alias_tag(ctx, new_tag, data["alias_of"])
    else:
        
        with open(filepath, "w") as file:
            data["aliases"].append(new_tag)
            json.dump(data, file)
    new_data, new_filepath = await get_tag_data(ctx, new_tag, False, False)
    if new_data == False: return

    new_data = {"name":new_tag,"type":"alias","alias_of":tag, "owner":str(ctx.author.id)}
    with open(new_filepath, "w") as file:
        json.dump(new_data, file)

    user = users.get_user_profile(str(ctx.author.id))
    user["tags"].append(new_tag)
    users.save_user_profile(user)

    return await ctx.reply(f":white_check_mark: Aliased **{new_tag}** to **{tag}**.")

async def list_tag(ctx, user):
    if user == "":
        return await list_all_tags(ctx)
    return await list_user_tags(ctx, user)
    
async def list_all_tags(ctx):
    tags = ""
    tag_count = 0
    for file in os.listdir(f"{DIR}/../../data/tags/tags"):
        if file.endswith(".json"):
            tags+=f"`{file[:-5]}`, "
            tag_count+=1
    if tags == "":
        return await ctx.reply("No tags found.")
    else: tags = tags[:-2]
    if len(tags) >= 2000:
        with open(f"{DIR}/../../data/tags/history/message.txt", "w") as file:
            file.write(tags)
            return await ctx.reply(f"**Tags in this server ({tag_count})**:", file=file)
    else:
        return await ctx.reply(f"**Tags in this server ({tag_count})**:\n{tags}")

async def list_user_tags(ctx, user):
    user = await users.resolve_user(ctx, user)
    if not user:
        return await ctx.reply(":warning: Couldn't find user.")
    tags = ""
    tag_count = 0
    for tag in user["tags"]:
        tags+=f"`{tag}`, "
        tag_count+=1
    if tags == "":
        return await ctx.reply(f"User <@{user["id"]}> has no tags.")
    else: tags = tags[:-2]
    if len(tags) >= 2000:
        with open(f"{DIR}/../../data/tags/history/message.txt", "w") as file:
            file.write(tags)
            return await ctx.reply(f"**<@{user["id"]}>'s tags ({tag_count})**:", file=file)
    else:
        return await ctx.reply(f"**<@{user["id"]}>'s tags ({tag_count})**:\n{tags}")

async def owner_tag(ctx, tag):
    if tag == "": return await ctx.reply(":information_source: %t owner `tag`")

    data, _ = await get_tag_data(ctx, tag, True, False)
    if data == False: return await ctx.reply(f":warning: Tag **{tag}** does not exist.")
    return await ctx.reply(f":information_source: Tag **{tag}** is owned by <@{data["owner"]}>.")

async def search_tag(ctx, search, amount):
    if search == "": return await ctx.reply(":information_source: %t search `query`")

    tags = os.listdir(f"{DIR}/../../data/tags/tags")
    tags = [tag for tag in tags if tag.endswith(".json")]
    distances = {}
    for tag in tags:
        tag = tag[:-5]
        distance = Levenshtein.distance(tag, search)
        distances[tag] = distance
    closest_match = heapq.nsmallest(amount, distances.items(), key=lambda item: item[1])
    out = ""
    for k, _ in closest_match:
        out += f"`{k}`, "
    return out[:-2]

async def raw_tag(ctx, tag):
    if tag == "": return await ctx.reply(":information_source: %t raw `tag`")

    data, filepath = await get_tag_data(ctx, tag, True, False)
    if data == False: return
    file = [discord.File(filepath)]
    if data["type"] == "code":
        file.append(discord.File(f"{filepath[:-5]}.py"))
    if data["type"] == "plaintext":
        file.append(discord.File(f"{filepath[:-5]}.txt"))
    return await ctx.reply(f":information_source: Raw data for {tag}.", files=file)
    
    
async def create_tag(ctx, tag_name, tag_body, filepath, success_text):

    # message tags
    if re.match("https:\/\/discord\.com\/channels\/\d+\/\d+\/\d+", tag_body):
        tag = {"name":tag_name,"type":"message","aliases":[],"message_link":tag_body, "owner":str(ctx.author.id)}
        with open(filepath, "w") as file:
            json.dump(tag, file)

    # code tags
    elif tag_body.startswith("```") and tag_body.endswith("```"):
        tag_body = tag_body[3:-3]
        if tag_body.startswith("py"):
            tag_body = tag_body[2:]
        if tag_body.startswith("thon"):
            tag_body =  tag_body[4:]
        tag = {"name":tag_name,"type":"code","aliases":[],"owner":str(ctx.author.id)}
        with open(filepath, "w") as file:
            json.dump(tag, file)
        with open(f"{filepath[:-5]}.py", "w", encoding="utf-8") as file:
            file.write(tag_body)
    # plaintext tags
    else:
        tag = {"name":tag_name,"type":"plaintext","aliases":[],"owner":str(ctx.author.id)}
        with open(filepath, "w") as file:
            json.dump(tag, file)
        with open(f"{filepath[:-5]}.txt", "w", encoding="utf-8") as file:
            file.write(tag_body)

    user = users.get_user_profile(str(ctx.author.id))
    user["tags"].append(tag_name)
    users.save_user_profile(user)

    return await ctx.reply(f":white_check_mark: {success_text} tag **{tag_name}**")

async def container(ctx, tag, message):
    container_name = uuid.uuid4().hex
    args = [str(ctx.author.id), ctx.author.name, str(ctx.channel.id)]
    if not message == None:
        args.extend(message)
    docargs = ['docker', 'run',
               '--name', container_name,
               '--memory', '512m',
               '--memory-swap', '512m',
               '--network', 'none',
               '--rm', '-v', f'{DIR}/../../data/tags/tags:/data/:ro',
               'python', 'python', f'/data/{tag}.py',
            ]
    docargs.extend(args)
    try:
        result = subprocess.run(
            docargs,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=5
        )
        output = result.stdout

        # output = output.decode(errors="replace")
    except subprocess.TimeoutExpired:
        # Force kill the container
        subprocess.run(
            ['docker', 'rm', '-f', container_name],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        output = "[PROCESS KILLED: exceeded 5s timeout]"
    except subprocess.CalledProcessError as e:
        output = e

    await ctx.reply(output)
