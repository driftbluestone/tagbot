import os
from discord.ext import commands
from pathlib import Path
from json import dump
from modules.tags import tag_utils
from modules.tags.users import get_user_profile, save_user_profile, resolve_user
DIR = Path(__file__).resolve().parent.parent.parent
VALID_NAME_CHARS = set("0123456789abcdefghijklmnopqrstuvwxyz_-")

async def tag_add(ctx: commands.Context, message: list):
    "Creates a tag while having safeguards to prevent overwriting"
    if not await tag_utils.check_creation_permission(ctx): return
    tag = message[0]
    if not tag: return await ctx.reply(":information_source: %t add `name` `body`")

    user_id = str(ctx.author.id)
    
    message = message[1:]
    data, _, exists, _ = await tag_utils.get_tag_data(user_id, tag)
    if exists:
        return await ctx.reply(f":warning: Tag {tag} already exists and is owned by <@{data["owner"]}>")
    if any(char not in VALID_NAME_CHARS for char in tag):
        return await ctx.reply(f":warning: Tag name must consist of characters a-z, 0-9, _, or -. ")
    sucess = await tag_utils.create_tag(user_id, tag, " ".join(message), f"{DIR}/data/tags/tags/{tag}.json")
    if not sucess: return await ctx.reply(f":warning: Tag body cannot be empty.")
    return await ctx.reply(f":white_check_mark: Created tag **{tag}**")

async def tag_edit(ctx: commands.Context, message: list, override: bool = False):
    """
    Edits a tag, if the tag is not found, it is created\n
    If override is enabled, it will ignore whether the user owns the tag or not.
    """
    if not await tag_utils.check_creation_permission(ctx): return
    if not tag: return await ctx.reply(":information_source: %t edit `name` `new body`")

    # Guiderails to prevent overwriting a tag you do not own.
    user_id = str(ctx.author.id)
    tag = message[0]
    message = message[1:]
    data, filepath, exists, owned = await tag_utils.get_tag_data(user_id, tag)
    if not exists:
        return await tag_add(ctx, message)
    if not (owned or override):
        return await ctx.reply(f":warning: Tag **{tag}** is owned by <@{data["owner"]}>")
    if override:
        user_id = data["owner"]

    # Remove the other files in case of a type change
    if data["type"] == "code":
        os.remove(f"{filepath[:-5]}.py")
    if data["type"] == "plaintext":
        os.remove(f"{filepath[:-5]}.txt")

    sucess = await tag_utils.create_tag(user_id, tag, " ".join(message), filepath)
    if not sucess: return await ctx.reply(f":warning: Tag body cannot be empty.")
    return await ctx.reply(f":white_check_mark: Edited tag **{tag}**")

async def tag_delete(ctx: commands.Context, tag: list, override: bool = False, silent: bool = False):
    """
    Deletes a tag\n
    Using override will make it ignore the owner\n
    Using silent will stop it from sending a message
    """
    tag = tag[0]
    if not tag: return await ctx.reply(":information_source: %t delete `tag`")

    user_id = str(ctx.author.id)
    data, filepath, exists, owned = await tag_utils.get_tag_data(user_id, tag)
    if not exists: return await ctx.reply(f":warning: Tag **{tag}** does not exist.")
    if not (owned or override):
        return await ctx.reply(f":warning: Tag **{tag}** is owned by <@{data["owner"]}>")

    # If the tag is not an alias itself, remove all aliases it has
    if data["type"] != "alias":
        aliases = data["aliases"]
        for alias in aliases:
            deleted_aliases = " and surrounding aliases"
            await tag_delete(ctx, alias, True, True)
    # If the tag is an alias, remove it from the parent tag
    else:
        alias_of, alias_filepath = await tag_utils.get_tag_data(ctx, data["alias_of"])
        alias_of["aliases"].remove(tag)
        with open(alias_filepath, "w") as file:
            dump(alias_of, file)
    
    # Remove other files from other tag types
    if data["type"] == "code":
        os.remove(f"{filepath[:-5]}.py")
    if data["type"] == "plaintext":
        os.remove(f"{filepath[:-5]}.txt")
    os.remove(filepath)

    # Save the data
    user = get_user_profile(data["owner"])
    user["tags"].remove(tag)
    save_user_profile(user)

    if not silent: return await ctx.reply(f":white_check_mark: Tag **{tag}**{deleted_aliases} deleted.")

async def tag_alias(ctx: commands.Context, message: list):
    "Creates an alias of another tag"
    can_create = await tag_utils.check_creation_permission(ctx)
    if not can_create: return

    new_tag: str = message[0]
    tag: str = message[1]
    if not new_tag: return await ctx.reply(":information_source: %t alias `new` `existing`")
    if not tag: return await ctx.reply(":warning: Please provide a tag to alias to.")

    user_id = str(ctx.author.id)
    data, filepath, exists, _ = await tag_utils.get_tag_data(user_id, tag)
    if not exists: return await ctx.reply(f":warning: Tag **{tag}** does not exist.")
    # If the tag is an alias, alias the new tag to the tag it's an alias of, as alias tags do not support being aliased
    if data["type"] == "alias":
        return await tag_alias(ctx, new_tag, data["alias_of"])

    with open(filepath, "w") as file:
        data["aliases"].append(new_tag)
        dump(data, file)
    new_data, new_filepath, exists, _  = await tag_utils.get_tag_data(ctx, new_tag)
    if exists: return await ctx.reply(f":warning: Tag {new_tag} already exists and is owned by <@{new_data["owner"]}>")

    new_data = {"name":new_tag,"type":"alias","alias_of":tag, "owner":str(ctx.author.id)}
    with open(new_filepath, "w") as file:
        dump(new_data, file)

    user = get_user_profile(str(ctx.author.id))
    user["tags"].append(new_tag)
    save_user_profile(user)

    return await ctx.reply(f":white_check_mark: Aliased **{new_tag}** to **{tag}**.")

async def tag_list(ctx: commands.Context, message: list):
    "this function is cursed."
    message = message[0]
    if message:
        user = await resolve_user(ctx, message)
        if not user: return await ctx.reply(":warning: Couldn't find user.")
        tag_list = user["tags"]
        tags = f"`{"`, `".join([x for x in tag_list])}`"
    else:
        tag_list = [x[:-5] for x in os.listdir(f"{DIR}/data/tags/tags") if x.endswith(".json")]
        tags = f"`{"`, `".join(tag_list)}`"
    tag_count = len(tag_list)
    if (not tag_list) and message:
        return await ctx.reply(f"User <@{user["id"]}> has no tags.")
    if not tag_list and not message:
        return await ctx.reply(f"No tags found.")
    if len(tags) >= 1900:
        with open(f"{DIR}/../../data/tags/history/message.txt", "w") as file:
            file.write(tags)
            if message: return await ctx.reply(f"**<@{user["id"]}>'s tags ({tag_count})**:", file=file)
            else: return await ctx.reply(f"**Tags in this server ({tag_count})**:", file=file)
    else:
        if message: return await ctx.reply(f"**<@{user["id"]}>'s tags ({tag_count})**:\n{tags}")
        else: return await ctx.reply(f"**Tags in this server ({tag_count})**:\n{tags}")

async def tag_owner(ctx: commands.Context, message: list):
    tag: str = message[0]
    if not tag: return await ctx.reply(":information_source: %t owner `tag`")
    data = (await tag_utils.get_tag_data(ctx, tag))[0]
    if not data: return await ctx.reply(f":warning: Tag **{tag}** does not exist.")
    return await ctx.reply(f":information_source: Tag **{tag}** is owned by <@{data["owner"]}>.")