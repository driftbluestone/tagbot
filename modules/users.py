import pathlib, json

DIR = pathlib.Path(__file__).resolve().parent

with open(f"{DIR}/configs/user.json", "r") as file:
    default_user_config = json.load(file)
with open(f"{DIR}/configs/permissions.json", "r") as file:
    default_user_permissions = json.load(file)

# these are different functions because all of them need to be accessed at some point
async def get_user_profile(user_id):
    filepath = f"{DIR}/../users/{user_id}.json"
    if pathlib.Path(filepath).exists():
        with open(filepath, "r") as file:
            user = json.load(file)
        return user
    else:
        user = default_user_config
        user["id"] = user_id
        return await permissions(user)
async def permissions(user):
    for k, v in default_user_permissions.items():
        if k not in user["permissions"].keys():
            user["permissions"][k] = v
    return await save_user_profile(user)
async def save_user_profile(user):
    filepath = f"{DIR}/../users/{user["id"]}.json"
    with open(filepath, "w") as file:
        json.dump(user, file)
    return user

async def permission_check(user, permission):
    try:
        return user["permissions"][permission]
    except:
        permissions(user)

async def resolve_user(ctx, user):
    if user.startswith("<@") and user.endswith(">"):
        user = user[2:-1]
        user_object = await ctx.bot.fetch_user(user)
    else:
        user_object = ctx.guild.get_member_named(user)
    if user_object == None:
        try:
            user = int(user)
            user_object = await ctx.bot.fetch_user(user)
        except: return False
    if user_object == None:
            return False
    return await get_user_profile(user_object.id)
    