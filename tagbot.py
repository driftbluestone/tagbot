import discord, os
import re
import json
import discord, os, re, datetime
from json import dump, load
from discord.ext import commands
from pathlib import Path

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
DIR = Path(__file__).resolve().parent

with open(DIR / "TOKEN.txt", "r", encoding="utf-8") as file:
    TOKEN = file.read().strip()

def ensure_store(tag_type: str) -> None:
    """Ensure ./tags/<tag_type>/ and its json files exist, and are loaded."""
    base = DIR / "tags" / tag_type
    base.mkdir(parents=True, exist_ok=True)
    defaults = {
        "admins.json": [True, []] if tag_type != "global_tags" else [False, []],
        "users.json": {},
        "tags.json": {},
    }

    for fname, default in defaults.items():
        path = base / fname
        if not path.exists():
            with open(path, "w", encoding="utf-8") as f:
                dump(default, f, ensure_ascii=False, indent=2)

    with open(base / "tags.json", "r", encoding="utf-8") as f:
        tags[tag_type] = load(f)
    with open(base / "admins.json", "r", encoding="utf-8") as f:
        admins[tag_type] = load(f)
    with open(base / "users.json", "r", encoding="utf-8") as f:
        users[tag_type] = load(f)

(DIR / "tags").mkdir(exist_ok=True)
ensure_store("global_tags")

# Load all existing per-server stores
for entry in os.listdir(DIR / "tags"):
    path = DIR / "tags" / entry
    if path.is_dir() and entry != "global_tags":
        ensure_store(entry)

unique_tags = ["add", "edit", "delete", "admin", "alias", "list", "owner"]
chars = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0',
         'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j',
         'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't',
         'u', 'v', 'w', 'x', 'y', 'z', '_', '-']

@bot.event
async def on_ready():
    print(f'Tagging it up as {bot.user}!')

@bot.event
async def on_message(message: discord.Message):
    # Keep commands working
    if message.author.bot:
        return

    if message.content.startswith("sed/") and message.reference is None:
        parts = message.content.split("/", 3)
        # sed/<pattern>/<replace>/[g]
        # parts: ["sed", pattern, replace, rest(optional)]
        if len(parts) < 3:
            try:
                await message.add_reaction("❌")
            finally:
                await bot.process_commands(message)
            return

        pattern = parts[1]
        replace = parts[2]
        rest = parts[3] if len(parts) == 4 else ""

        if not pattern:
            try:
                await message.add_reaction("❌")
            finally:
                await bot.process_commands(message)
            return

        # determine global flag
        global_flag = rest.strip().startswith("g")
        count = 0 if global_flag else 1

        # Find a previous message in history that matches the pattern
        replied_message = None
        try:
            async for m in message.channel.history(limit=25):
                if m.id == message.id:
                    continue
                if m.author.bot:
                    continue
                if m.content.startswith("sed/"):
                    continue
                try:
                    if re.search(pattern, m.content):
                        replied_message = m
                        break
                except re.error:
                    replied_message = None
                    break

            if replied_message is None:
                await message.add_reaction("❌")
            else:
                try:
                    sub = re.sub(pattern, replace, replied_message.content, count=count)
                except re.error:
                    await message.add_reaction("❌")
                else:
                    embed = discord.Embed(description=sub, color=0x222222)
                    embed.set_author(
                        name=str(replied_message.author),
                        icon_url=(
                            replied_message.author.avatar.url if replied_message.author.avatar else discord.Embed.Empty),
                    )
                    embed.set_footer(text=f"sed replace in #{message.channel}")
                    await message.channel.send(embed=embed)

        except discord.Forbidden:
            pass
        except discord.HTTPException:
            pass

    await bot.process_commands(message)

@bot.command(name="t")
async def t(ctx, tag: str = None, *args):
    await get_tag(ctx, tag, args)

@bot.command(name="tag")
async def tag(ctx, tag: str = None, *args):
    await get_tag(ctx, tag, args)

async def get_tag(ctx, tag, args):

if tag == None:
    return await ctx.reply(f":information_source: %t `add|edit|delete|admin|alias|list|owner`")

# Allow: %t @user  -> list that user's tags (server tags)
if ctx.guild is not None and isinstance(tag, str):
    uid = resolve_user_id(ctx, tag)
    # Only treat as user-target when it's a mention or pure numeric ID token
    if uid is not None and (re.fullmatch(r"<@!?\d+>", tag.strip()) or tag.strip().isdigit()):
        items = await list_tags_for_owner(ctx, str(ctx.guild.id), uid)
        return await reply_in_chunks(ctx, f"**Tags for {format_user_no_ping(ctx, uid)}:**", items)

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
with open(f"{DIR}/tags/{tag_type}/{tag}.txt", "r", encoding="utf-8") as file:
    body = file.read()
return await ctx.reply(body)

def admins_path(server_id: str) -> Path:
    return DIR / "tags" / server_id / "admins.json"

def save_admins(server_id: str, admins_obj):
    p = admins_path(server_id)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as f:
        json.dump(admins_obj, f, ensure_ascii=False, indent=2)

def can_manage_admins(ctx) -> bool:
    return ctx.guild and (ctx.author == ctx.guild.owner or ctx.author.guild_permissions.manage_guild)

def resolve_user_id(ctx, token: str) -> int | None:
    # <@123> o <@!123>
    m = re.fullmatch(r"<@!?(\d+)>", token.strip())
    if m:
        return int(m.group(1))
    # ID
    if token.isdigit():
        return int(token)

    member = ctx.guild.get_member_named(token)
    return member.id if member else None

def format_user_no_ping(ctx, user_id: int) -> str:
    m = ctx.guild.get_member(user_id)
    return f"{m.display_name} ({user_id})" if m else str(user_id)

def is_bot_admin(ctx) -> bool:
    if not ctx.guild:
        return False
    sid = str(ctx.guild.id)
    uid = str(ctx.author.id)

    if ctx.author == ctx.guild.owner:
        return True
    if getattr(ctx.author, "guild_permissions", None):
        if ctx.author.guild_permissions.administrator or ctx.author.guild_permissions.manage_guild:
            return True

    try:
        return uid in [str(x) for x in admins.get(sid, [True, []])[1]]
    except Exception:
        return False

async def has_permission(ctx, tag_type: str) -> bool:
    """Return True if the user is allowed to create/edit tags for tag_type."""
    uid = str(ctx.author.id)

    # only global admins
    if tag_type == "global_tags":
        return uid in admins["global_tags"][1]

    # anyone can create tags
    if admins.get(tag_type, [False, []])[0]:
        return True

    # ot-admin list or Discord server admins
    if uid in admins.get(tag_type, [False, []])[1]:
        return True
    if getattr(ctx.author, "guild_permissions", None) and ctx.author.guild_permissions.administrator:
        return True
    return False

async def dump_tag(body, name, tag_type):
    with open(f"{DIR}/tags/{tag_type}/{name}.txt", "w", encoding="utf-8") as file:
        file.write(body)

async def generate_files(server_id: str) -> None:
    ensure_store(server_id)

async def generate_metadata(tag_type, tag, user_id, alias):
    if alias == "":
        tag_meta = [user_id, [], False]
    else:
        tag_meta = [user_id, alias, True]
    tags[tag_type][tag] = tag_meta
    with open(f"{DIR}/tags/{tag_type}/tags.json", "w", encoding="utf-8") as file:
        dump(tags[tag_type], file, ensure_ascii=False, indent=2)
    users[tag_type][user_id] = users[tag_type].get(user_id, [])
    users[tag_type][user_id].append(tag)
    users[tag_type][user_id].sort()
    with open(f"{DIR}/tags/{tag_type}/users.json", "w", encoding="utf-8") as file:
        dump(users[tag_type], file, ensure_ascii=False, indent=2)

async def is_moderator(ctx, tag_type: str) -> bool:
    """Return True if ctx.author can manage other users' tags in tag_type."""
    uid = str(ctx.author.id)
    if tag_type == "global_tags":
        return uid in admins["global_tags"][1]
    return bool(ctx.author.guild_permissions.administrator or (uid in admins[tag_type][1]))

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
        if not is_bot_admin(ctx):
            return await ctx.reply(":warning: No permission.", mention_author=False)
        return await admin_function(ctx, args)
    elif tag == "alias":
        return await alias_tag(ctx, args)
    elif tag == "owner":
        if args == ():
            return await ctx.reply(":information_source: %t owner `tag`")
        return await owner_tag(ctx, args[0], await tag_owner(args[0], await get_tag_type(ctx, args[0])),
                               ":information_source:")
    elif tag == "list":
        # %t list -> list all server tags
        if len(args) == 0:
            tag_type = str(ctx.guild.id)
            items = await list_all_tags(tag_type, include_aliases=False)
            return await reply_in_chunks(ctx, f"**Tags in this server ({len(items)}):**", items)

        # %t list global [@user|id|name]
        if len(args) >= 1 and args[0] in ("global", "global_tags"):
            if len(args) == 1:
                items = await list_all_tags("global_tags", include_aliases=False)
                return await reply_in_chunks(ctx, f"**Global tags ({len(items)}):**", items)

            uid = resolve_user_id(ctx, args[1])
            if uid is None:
                return await ctx.reply(":warning: Couldn't resolve that user.", mention_author=False)
            items = await list_tags_for_owner(ctx, "global_tags", uid)
            return await reply_in_chunks(ctx, f"**Global tags for {format_user_no_ping(ctx, uid)}:**", items)

        # %t list <@user|id|name> -> list tags owned by that user (server tags)
        uid = resolve_user_id(ctx, args[0])
        if uid is None:
            return await ctx.reply(":warning: Couldn't resolve that user.", mention_author=False)

        tag_type = str(ctx.guild.id)
        items = await list_tags_for_owner(ctx, tag_type, uid)
        return await reply_in_chunks(ctx, f"**Tags for {format_user_no_ping(ctx, uid)}:**", items)

async def admin_function(ctx, args):
    if not is_bot_admin(ctx):
        return await ctx.reply(":warning: No permission.", mention_author=False)
    user_id = str(ctx.author.id)
    server_id = str(ctx.guild.id)
    await generate_files(server_id)
    if args == ():
        return await ctx.reply(":information_source: %t admin `delete|promote|limit`")
    tag = args[0]
    if tag == "delete":
        return await delete_tag(ctx, args[1:], False)
    elif tag == "promote":
        return await admin_promote(ctx, args[1:])
    elif tag == "limit":
        return await limit_to_admins(ctx)
    else:
        return await ctx.reply(":warning: Invalid admin subcommand.")

async def add_tag(ctx, args, cont):
    server_id = str(ctx.guild.id)
    if args == ():
        if not await has_permission(ctx, server_id):
            return await ctx.reply(":warning: No permission.")
        return await ctx.reply(":information_source: %t add `name` `body`")

    user_id = str(ctx.author.id)
    name = str(args[0]).lower()
    tag_type = server_id
    if name.startswith("*"):
        tag_type = "global_tags"
        name = name[1:]
    await generate_files(server_id)
    if not await has_permission(ctx, tag_type):
        return await ctx.reply(":warning: No permission.")
    if any(char not in chars for char in name):
        return await ctx.reply(f":warning: Tag name must consist of characters a-z, 0-9, _, or -. ")

    if name in unique_tags:
        return await ctx.reply(f":warning: Tag {name} already exists.")
    tags[tag_type] = tags.get(tag_type, {})
    if name in tags["global_tags"]:
        return await ctx.reply(
            f":warning: Tag **{name}** already exists, and is owned by {format_user_no_ping(ctx, int(tags['global_tags'][name][0]))}.", mention_author=False)
    if (not tag_type == "global_tags") and (name in tags[server_id]):
        return await ctx.reply(
            f":warning: Tag **{name}** already exists, and is owned by {format_user_no_ping(ctx, int(tags[server_id][name][0]))}.", mention_author=False)
    body = " ".join(args[1:]).strip()
    if body == "" or body == " ":
        return await ctx.reply(":warning: Tag body is empty.")
    await generate_metadata(tag_type, name, user_id, "")
    await dump_tag(body, name, tag_type)

    return await ctx.reply(f"✅ Added tag {name}!")

async def edit_tag(ctx, args, cont):
    if args == ():
        return await ctx.reply(":information_source: %t edit `name` `new_body`")
    user_id = str(ctx.author.id)
    name = str(args[0]).lower()
    tag_type = await get_tag_type(ctx, name)
    if tag_type is False:
        return await ctx.reply(f":warning: Tag {name} doesn't exist.")
    if tag_type == "global_tags" and name.startswith("*"):
        name = name[1:]

    if tags[tag_type][name][2]:
        target = tags[tag_type][name][1]
        if target.startswith("*"):
            tag_type = "global_tags"
            name = target[1:]
        else:
            name = target

    owner = await tag_owner(name, tag_type)
    if owner != user_id and not await is_moderator(ctx, tag_type):
        return await owner_tag(ctx, name, owner, ":warning:")

    body = " ".join(args[1:]).strip()
    if not body:
        return await ctx.reply(":warning: Tag body is empty.")
    await dump_tag(body, name, tag_type)
    return await ctx.reply(f"✅ Edited tag {name}.")

async def delete_tag(ctx, args, check_ownership):
    if args == ():
        return await ctx.reply(":information_source: %t delete `tag`")
    user_id = str(ctx.author.id)
    tag = args[0]
    tag_type = await get_tag_type(ctx, tag)
    if tag_type is False:
        return await ctx.reply(f":warning: Tag **{tag}** doesn't exist.")
    owner = await tag_owner(tag, tag_type)
    if check_ownership and owner != user_id and not await is_moderator(ctx, tag_type):
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
        with open(f"{DIR}/tags/{tag_type}/tags.json", "w", encoding="utf-8") as file:
            dump(tags[tag_type], file, ensure_ascii=False, indent=2)
        with open(f"{DIR}/tags/{tag_type}/users.json", "w", encoding="utf-8") as file:
            dump(users[tag_type], file, ensure_ascii=False, indent=2)
    return await ctx.reply(f"✅ Tag **{tag}** {aliased}deleted.")

async def admin_promote(ctx, args):
    server_id = str(ctx.guild.id)
    if args == ():
        descbuilder = ""
        x = 1
        for i in admins[server_id][1]:
            descbuilder += f"{x}. {format_user_no_ping(ctx, int(i))}"
        if len(descbuilder) >= 3900:
            with open(f"{DIR}/message.txt", "w", encoding="utf-8") as file:
                file.write(descbuilder)
                return await ctx.reply(f":information_source: %t admin promote `@user|username`\nAdmins:", file=file)
        reply = ""
        if descbuilder != "":
            reply = "Admins:\n"
        return await ctx.reply(f":information_source: %t admin promote `@user|username`\n{reply}{descbuilder}")

    user = args[0]
    promote_type = str(ctx.guild.id)
    if user.startswith("*"):
        if not await has_permission(ctx, "global_tags"):
            return await ctx.reply(f":warning: You can't promote a user to global admin.")
        promote_type = "global_tags"
        user = user[1:]
    if user.startswith("<@"):
        user = user[2:-1]
    else:
        user = str(ctx.guild.get_member_named(user).id)

    if user in admins[promote_type][1]:
        admins[promote_type][1].remove(user)
        with open(f"{DIR}/tags/{promote_type}/admins.json", "w", encoding="utf-8") as file:
            dump(admins[promote_type], file, ensure_ascii=False, indent=2)
        return await ctx.reply(f"✅ Removed admin {format_user_no_ping(ctx, int(user))}.", mention_author=False)
    else:
        admins[promote_type][1].append(user)
        with open(f"{DIR}/tags/{promote_type}/admins.json", "w", encoding="utf-8") as file:
            dump(admins[promote_type], file, ensure_ascii=False, indent=2)
        return await ctx.reply(f"✅ Added admin {format_user_no_ping(ctx, int(user))}.", mention_author=False)

async def limit_to_admins(ctx):
    server_id = str(ctx.guild.id)
    await generate_files(server_id)
    if admins[server_id][0]:
        admins[server_id][0] = False
        with open(f"{DIR}/tags/{server_id}/admins.json", "w", encoding="utf-8") as file:
            dump(admins[server_id], file, ensure_ascii=False, indent=2)
        return await ctx.reply("✅ Only admins can now create tags.")
    else:
        admins[server_id][0] = True
        with open(f"{DIR}/tags/{server_id}/admins.json", "w", encoding="utf-8") as file:
            dump(admins[server_id], file, ensure_ascii=False, indent=2)
        return await ctx.reply("✅ Any user can now create tags.")

async def alias_tag(ctx, args):
    server_id = str(ctx.guild.id)
    if args == ():
        if not await has_permission(ctx, server_id):
            return await ctx.reply(":warning: No permission.")
        return await ctx.reply(":information_source: %t alias `new tag` `other tag`")
    user_id = str(ctx.author.id)
    new_tag = str(args[0]).lower()
    new_tag_type = server_id
    if new_tag.startswith("*"):
        new_tag_type = "global_tags"
        new_tag = new_tag[1:]
    if not await has_permission(ctx, new_tag_type):
        return await ctx.reply(":warning: No permission.")
    if new_tag in tags[new_tag_type]:
        return await ctx.reply(f":warning: Tag **{new_tag}** already exists.")
    try:
        old_tag = args[1]
    except:
        return await ctx.reply(":warning: Please provide a tag to alias to.")
    old_tag_type = server_id
    old_tag_2 = old_tag
    if old_tag.startswith("*"):
        old_tag_type = "global_tags"
        old_tag_2 = old_tag[1:]
    if new_tag_type == "global_tags" and not old_tag_type == "global_tags":
        return await ctx.reply(":warning: Can't alias a global tag to a local tag.")
    if any(char not in chars for char in new_tag):
        return await ctx.reply(f":warning: Tag name must consist of characters a-z, 0-9, _, or -. ")

    if not old_tag_2 in tags[old_tag_type]:
        return await ctx.reply(f":warning: Tag **{old_tag}** doesn't exist.")
    await generate_files(server_id)
    await generate_metadata(new_tag_type, new_tag, user_id, old_tag)
    tags[old_tag_type][old_tag_2][1].append(new_tag)
    with open(f"{DIR}/tags/{old_tag_type}/tags.json", "w", encoding="utf-8") as file:
        dump(tags[old_tag_type], file, ensure_ascii=False, indent=2)
    return await ctx.reply(f"✅ Aliased **{new_tag}** to **{old_tag_2}**.")

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
            num += 1
    except:
        pass
    try:
        for i in users[server_id][user]:
            descbuilder += f"{num}. {i}\n"
            num += 1
    except:
        pass
    if len(descbuilder) >= 3900:
        with open(f"{DIR}/message.txt", "w", encoding="utf-8") as file:
            file.write(descbuilder)
            return await ctx.reply(f":information_source: {format_user_no_ping(ctx, int(user))} has the following tags:", file=file, mention_author=False)
    if descbuilder == "":
        return await ctx.reply(f":information_source: {format_user_no_ping(ctx, int(user))} has no tags.", mention_author=False)
    return await ctx.reply(f":information_source: {format_user_no_ping(ctx, int(user))} has the following tags:\n{descbuilder}", mention_author=False)

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
    return await ctx.reply(f"{msg} Tag **{tag}** is owned by {format_user_no_ping(ctx, int(owner))}.", mention_author=False)

async def list_all_tags(tag_type: str, include_aliases: bool = False) -> list[str]:
    out = []
    if tag_type not in tags:
        return out
    for name, meta in tags[tag_type].items():
        try:
            is_alias = bool(meta[2])
        except Exception:
            is_alias = False
        if include_aliases or not is_alias:
            out.append(name)
    out.sort()
    return out

async def list_tags_for_owner(ctx, tag_type: str, owner_id: int) -> list[str]:
    out = []
    if tag_type not in tags:
        return out

    for name, meta in tags[tag_type].items():
        try:
            if int(meta[0]) == int(owner_id):
                out.append(name)
        except Exception:
            pass
    out.sort()
    return out

async def reply_in_chunks(ctx, header: str, items: list[str], chunk_size: int = 30):
    if not items:
        return await ctx.reply(header + "\n*(none)*", mention_author=False)
    for i in range(0, len(items), chunk_size):
        page = items[i:i + chunk_size]
        body = ", ".join(f"`{x}`" for x in page)
        await ctx.reply(f"{header}\n{body}", mention_author=False)

bot.run(TOKEN)