import discord
import os
import re
from json import dump, load
from discord.ext import commands
from pathlib import Path

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(
    command_prefix="%",
    allowed_mentions=discord.AllowedMentions(
        users=False,
        everyone=False,
        roles=False,
        replied_user=True,
    ),
    intents=intents,
)

tags, admins, users = {}, {}, {}
DIR = Path(__file__).resolve().parent

with open(DIR / "TOKEN.txt", "r", encoding="utf-8") as file:
    TOKEN = file.read().strip()

def ensure_store(tag_type: str) -> None:
    """Ensure ./tags/<tag_type>/ exists, create json files if missing, and load them."""
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

UNIQUE_TAGS = ["add", "edit", "delete", "admin", "alias", "list", "owner"]
VALID_NAME_CHARS = set("0123456789abcdefghijklmnopqrstuvwxyz_-")

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}.")


@bot.event
async def on_message(message: discord.Message):
    # Keep commands working
    if message.author.bot:
        return

    # sed/<pattern>/<replace>/[g]
    if message.content.startswith("sed/") and message.reference is None:
        parts = message.content.split("/", 3)
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

        global_flag = rest.strip().startswith("g")
        count = 0 if global_flag else 1

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
                            replied_message.author.avatar.url
                            if replied_message.author.avatar
                            else discord.Embed.Empty
                        ),
                    )
                    embed.set_footer(text=f"sed replace in #{message.channel}")
                    await message.channel.send(embed=embed)

        except (discord.Forbidden, discord.HTTPException):
            pass

    await bot.process_commands(message)

def resolve_user_id_token(token: str):
    tok = token.strip()
    m = re.fullmatch(r"<@!?(\d+)>", tok)
    if m:
        return int(m.group(1))
    if tok.isdigit():
        return int(tok)
    return None

def format_user_no_ping(ctx, user_id: int) -> str:
    if ctx.guild:
        m = ctx.guild.get_member(user_id)
        if m:
            return f"{m.display_name} ({user_id})"
    return str(user_id)

def is_bot_admin(ctx) -> bool:
    if not ctx.guild:
        return False
    sid = str(ctx.guild.id)
    uid = str(ctx.author.id)

    if ctx.author == ctx.guild.owner:
        return True
    perms = getattr(ctx.author, "guild_permissions", None)
    if perms and (perms.administrator or perms.manage_guild):
        return True

    try:
        return uid in [str(x) for x in admins.get(sid, [True, []])[1]]
    except Exception:
        return False

async def has_permission(ctx, tag_type: str) -> bool:
    uid = str(ctx.author.id)

    # Global tags are limited to global admins
    if tag_type == "global_tags":
        return uid in admins["global_tags"][1]

    # If open_to_all is True, anyone can create tags
    if admins.get(tag_type, [False, []])[0]:
        return True

    # Otherwise: bot-admin list or Discord administrators
    if uid in admins.get(tag_type, [False, []])[1]:
        return True
    perms = getattr(ctx.author, "guild_permissions", None)
    if perms and perms.administrator:
        return True

    return False

async def is_moderator(ctx, tag_type: str) -> bool:
    uid = str(ctx.author.id)
    if tag_type == "global_tags":
        return uid in admins["global_tags"][1]
    perms = getattr(ctx.author, "guild_permissions", None)
    return bool((perms and perms.administrator) or (uid in admins[tag_type][1]))

async def get_tag_type(ctx, name: str):
    server_id = str(ctx.guild.id)

    if name.startswith("*") and name[1:] in tags["global_tags"]:
        return "global_tags"
    if name in tags.get(server_id, {}):
        return server_id
    if name in tags["global_tags"]:
        return "global_tags"
    return False

async def dump_tag(body: str, name: str, tag_type: str):
    with open(f"{DIR}/tags/{tag_type}/{name}.txt", "w", encoding="utf-8") as file:
        file.write(body)

async def generate_files(server_id: str) -> None:
    ensure_store(server_id)

async def generate_metadata(tag_type: str, tag: str, user_id: str, alias: str):
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

async def tag_owner(tag: str, tag_type):
    if tag in UNIQUE_TAGS:
        return "unique"
    if tag_type is False:
        return False
    return tags[tag_type][tag][0]

async def owner_tag(ctx, tag: str, owner, msg: str):
    if owner == "unique":
        return await ctx.reply(f"{msg} Tag **{tag}** is a reserved command.")
    if owner is False:
        return await ctx.reply(f"{msg} Tag **{tag}** doesn't exist.")
    return await ctx.reply(
        f"{msg} Tag **{tag}** is owned by {format_user_no_ping(ctx, int(owner))}.",
        mention_author=False,
    )

async def list_all_tags(tag_type: str, include_aliases: bool = False) -> list:
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

async def list_tags_for_owner(ctx, tag_type: str, owner_id: int) -> list:
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

async def reply_in_chunks(ctx, header: str, items: list, chunk_size: int = 30):
    if not items:
        return await ctx.reply(header + "\n*(none)*", mention_author=False)

    for i in range(0, len(items), chunk_size):
        page = items[i : i + chunk_size]
        body = ", ".join(f"`{x}`" for x in page)
        await ctx.reply(f"{header}\n{body}", mention_author=False)

@bot.command(name="t")
async def t(ctx, tag: str = None, *args):
    await get_tag(ctx, tag, args)

@bot.command(name="tag")
async def tag(ctx, tag: str = None, *args):
    await get_tag(ctx, tag, args)

async def get_tag(ctx, tag, args):
    if tag is None:
        return await ctx.reply(":information_source: %t `add|edit|delete|admin|alias|list|owner`")

    # Allow: %t @user  -> list that user's tags (server tags)
    if ctx.guild is not None and isinstance(tag, str):
        uid = resolve_user_id_token(tag)
        if uid is not None:
            items = await list_tags_for_owner(ctx, str(ctx.guild.id), uid)
            return await reply_in_chunks(ctx, f"**Tags for {format_user_no_ping(ctx, uid)}:**", items)

    if tag in UNIQUE_TAGS:
        return await unique_tag(ctx, tag, args, ctx.message.content)

    tag_type = await get_tag_type(ctx, tag)
    if tag_type is False:
        return await ctx.reply(f":warning: Tag {tag} doesn't exist.")

    # normalize global form
    if tag_type == "global_tags" and tag.startswith("*"):
        tag = tag[1:]

    # resolve alias to its target
    if tags[tag_type][tag][2]:
        tag = tags[tag_type][tag][1]
        if tag.startswith("*"):
            tag_type = "global_tags"
            tag = tag[1:]

    with open(f"{DIR}/tags/{tag_type}/{tag}.txt", "r", encoding="utf-8") as file:
        body = file.read()

    return await ctx.reply(body)

async def unique_tag(ctx, tag, args, cont):
    if tag == "add":
        return await add_tag(ctx, args, cont)
    if tag == "edit":
        return await edit_tag(ctx, args, cont)
    if tag == "delete":
        return await delete_tag(ctx, args, True)
    if tag == "admin":
        if not is_bot_admin(ctx):
            return await ctx.reply(":warning: No permission.", mention_author=False)
        return await admin_function(ctx, args)
    if tag == "alias":
        return await alias_tag(ctx, args)
    if tag == "owner":
        if args == ():
            return await ctx.reply(":information_source: %t owner `tag`")
        return await owner_tag(ctx, args[0], await tag_owner(args[0], await get_tag_type(ctx, args[0])), ":information_source:")
    if tag == "list":
        # %t list -> list all server tags
        if len(args) == 0:
            tag_type = str(ctx.guild.id)
            items = await list_all_tags(tag_type, include_aliases=False)
            return await reply_in_chunks(ctx, f"**Tags in this server ({len(items)}):**", items)

        # %t list global [@user|id]
        if len(args) >= 1 and args[0] in ("global", "global_tags"):
            if len(args) == 1:
                items = await list_all_tags("global_tags", include_aliases=False)
                return await reply_in_chunks(ctx, f"**Global tags ({len(items)}):**", items)

            uid = resolve_user_id_token(args[1])
            if uid is None:
                return await ctx.reply(":warning: Couldn't resolve that user.", mention_author=False)
            items = await list_tags_for_owner(ctx, "global_tags", uid)
            return await reply_in_chunks(ctx, f"**Global tags for {format_user_no_ping(ctx, uid)}:**", items)

        # %t list <@user|id> -> list server tags for that user
        uid = resolve_user_id_token(args[0])
        if uid is None:
            return await ctx.reply(":warning: Couldn't resolve that user.", mention_author=False)
        tag_type = str(ctx.guild.id)
        items = await list_tags_for_owner(ctx, tag_type, uid)
        return await reply_in_chunks(ctx, f"**Tags for {format_user_no_ping(ctx, uid)}:**", items)

async def admin_function(ctx, args):
    if not is_bot_admin(ctx):
        return await ctx.reply(":warning: No permission.", mention_author=False)

    server_id = str(ctx.guild.id)
    await generate_files(server_id)

    if args == ():
        return await ctx.reply(":information_source: %t admin `delete|promote|limit`")
    sub = args[0].lower()
    if sub == "delete":
        return await delete_tag(ctx, args[1:], False)
    if sub == "promote":
        return await admin_promote(ctx, args[1:])
    if sub == "limit":
        return await limit_to_admins(ctx)

    return await ctx.reply(":warning: Invalid admin subcommand. Use: delete|promote|limit", mention_author=False)

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

async def admin_promote(ctx, args):
    server_id = str(ctx.guild.id)

    if args == ():
        desc = ""
        x = 1
        for i in admins[server_id][1]:
            desc += f"{x}. {format_user_no_ping(ctx, int(i))}\n"
            x += 1
        if not desc:
            desc = "(none)"
        return await ctx.reply(
            f":information_source: %t admin promote `<@user|id>`\nAdmins:\n{desc}",
            mention_author=False,
        )

    promote_type = server_id
    token = args[0]

    if token.startswith("*"):
        if not await has_permission(ctx, "global_tags"):
            return await ctx.reply(":warning: You can't promote a user to global admin.")
        promote_type = "global_tags"
        token = token[1:]

    uid = resolve_user_id_token(token)
    if uid is None:
        return await ctx.reply(":warning: Please provide a user mention or numeric ID.", mention_author=False)

    uid_s = str(uid)
    if uid_s in admins[promote_type][1]:
        admins[promote_type][1].remove(uid_s)
        with open(f"{DIR}/tags/{promote_type}/admins.json", "w", encoding="utf-8") as file:
            dump(admins[promote_type], file, ensure_ascii=False, indent=2)
        return await ctx.reply(f"✅ Removed admin {format_user_no_ping(ctx, uid)}.", mention_author=False)
    else:
        admins[promote_type][1].append(uid_s)
        with open(f"{DIR}/tags/{promote_type}/admins.json", "w", encoding="utf-8") as file:
            dump(admins[promote_type], file, ensure_ascii=False, indent=2)
        return await ctx.reply(f"✅ Added admin {format_user_no_ping(ctx, uid)}.", mention_author=False)

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

    if any(ch not in VALID_NAME_CHARS for ch in name):
        return await ctx.reply(":warning: Tag names may only contain a-z, 0-9, _, or -.")

    if name in UNIQUE_TAGS:
        return await ctx.reply(f":warning: Tag {name} is reserved.")

    tags[tag_type] = tags.get(tag_type, {})

    if name in tags["global_tags"]:
        return await ctx.reply(
            f":warning: Tag **{name}** already exists and is owned by {format_user_no_ping(ctx, int(tags['global_tags'][name][0]))}.",
            mention_author=False,
        )
    if tag_type != "global_tags" and name in tags.get(server_id, {}):
        return await ctx.reply(
            f":warning: Tag **{name}** already exists and is owned by {format_user_no_ping(ctx, int(tags[server_id][name][0]))}.",
            mention_author=False,
        )

    body = " ".join(args[1:]).strip()
    if not body:
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
    tag = args[0].lower()

    tag_type = await get_tag_type(ctx, tag)
    if tag_type is False:
        return await ctx.reply(f":warning: Tag **{tag}** doesn't exist.")

    owner = await tag_owner(tag, tag_type)
    if check_ownership and owner != user_id and not await is_moderator(ctx, tag_type):
        return await owner_tag(ctx, tag, owner, ":warning:")

    aliased_msg = ""

    if tags[tag_type][tag][2]:
        target = tags[tag_type][tag][1]
        if target in tags[tag_type] and isinstance(tags[tag_type][target][1], list):
            if tag in tags[tag_type][target][1]:
                tags[tag_type][target][1].remove(tag)
        tags[tag_type].pop(tag, None)
        if user_id in users.get(tag_type, {}) and tag in users[tag_type].get(user_id, []):
            users[tag_type][user_id].remove(tag)

    else:
        for alias in list(tags[tag_type][tag][1]):
            try:
                alias_owner = tags[tag_type][alias][0]
                if alias_owner in users.get(tag_type, {}) and alias in users[tag_type][alias_owner]:
                    users[tag_type][alias_owner].remove(alias)
                tags[tag_type].pop(alias, None)
            except Exception:
                pass

        tags[tag_type].pop(tag, None)
        if user_id in users.get(tag_type, {}) and tag in users[tag_type][user_id]:
            users[tag_type][user_id].remove(tag)

        try:
            os.remove(f"{DIR}/tags/{tag_type}/{tag}.txt")
        except FileNotFoundError:
            pass

        aliased_msg = " and its aliases"

    with open(f"{DIR}/tags/{tag_type}/tags.json", "w", encoding="utf-8") as file:
        dump(tags[tag_type], file, ensure_ascii=False, indent=2)
    with open(f"{DIR}/tags/{tag_type}/users.json", "w", encoding="utf-8") as file:
        dump(users[tag_type], file, ensure_ascii=False, indent=2)

    return await ctx.reply(f"✅ Deleted tag **{tag}**{aliased_msg}.")

async def alias_tag(ctx, args):
    server_id = str(ctx.guild.id)

    if args == ():
        if not await has_permission(ctx, server_id):
            return await ctx.reply(":warning: No permission.")
        return await ctx.reply(":information_source: %t alias `new_tag` `existing_tag`")

    user_id = str(ctx.author.id)
    new_tag = str(args[0]).lower()
    new_tag_type = server_id

    if new_tag.startswith("*"):
        new_tag_type = "global_tags"
        new_tag = new_tag[1:]

    if not await has_permission(ctx, new_tag_type):
        return await ctx.reply(":warning: No permission.")

    if any(ch not in VALID_NAME_CHARS for ch in new_tag):
        return await ctx.reply(":warning: Tag names may only contain a-z, 0-9, _, or -.")

    if new_tag in tags.get(new_tag_type, {}):
        return await ctx.reply(f":warning: Tag **{new_tag}** already exists.")

    if len(args) < 2:
        return await ctx.reply(":warning: Please provide a tag to alias to.")

    old_tag = str(args[1]).lower()
    old_tag_type = server_id
    old_tag_key = old_tag

    if old_tag.startswith("*"):
        old_tag_type = "global_tags"
        old_tag_key = old_tag[1:]

    if new_tag_type == "global_tags" and old_tag_type != "global_tags":
        return await ctx.reply(":warning: Can't alias a global tag to a local tag.")

    if old_tag_key not in tags.get(old_tag_type, {}):
        return await ctx.reply(f":warning: Tag **{old_tag}** doesn't exist.")

    await generate_files(server_id)
    await generate_metadata(new_tag_type, new_tag, user_id, old_tag)

    if isinstance(tags[old_tag_type][old_tag_key][1], list):
        tags[old_tag_type][old_tag_key][1].append(new_tag)

    with open(f"{DIR}/tags/{old_tag_type}/tags.json", "w", encoding="utf-8") as file:
        dump(tags[old_tag_type], file, ensure_ascii=False, indent=2)

    return await ctx.reply(f"✅ Aliased **{new_tag}** to **{old_tag_key}**.")

bot.run(TOKEN)