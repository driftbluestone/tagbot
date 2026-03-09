import discord, pathlib, json, math
from modules import config
DIR = pathlib.Path(__file__).resolve().parent

with open(f"{DIR}/configs/user.json", "r") as file:
    default_user_config = json.load(file)
with open(f"{DIR}/configs/permissions.json", "r") as file:
    default_user_permissions = json.load(file)
with open(f"{DIR}/../../data/static/permissions.json", "r") as file:
    user_permission_equivalent = json.load(file)

# these are different functions because all of them need to be accessed at some point
def get_user_profile(user_id):
    filepath = f"{DIR}/../../data/tags/users/{user_id}.json"
    if pathlib.Path(filepath).exists():
        with open(filepath, "r") as file:
            user = json.load(file)
        return user
    else:
        user = default_user_config
        user["id"] = user_id
        return permissions(user)
def permissions(user):
    for k, v in default_user_permissions.items():
        if k not in user["permissions"].keys():
            user["permissions"][k] = v
    return save_user_profile(user)
def save_user_profile(user):
    filepath = f"{DIR}/../../data/tags/users/{user["id"]}.json"
    with open(filepath, "w") as file:
        json.dump(user, file)
    return user

async def permission_check(user, permission):
    user_profile = get_user_profile(user.id)
    try:
        profile_permission = user_profile["permissions"][permission]
    except:
        user_profile = permissions(user_profile)
        profile_permission = user_profile["permissions"][permission]
    discord_permissions = getattr(user.guild_permissions, user_permission_equivalent[permission], False)
    return discord_permissions or profile_permission
    
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
    return get_user_profile(user_object.id)

class PermissionPanel(discord.ui.View):
    def __init__(self, old_interaction, user, page = 1):
        super().__init__(timeout=1000000000)
        self.old_interaction: discord.Interaction = old_interaction
        self.user: discord.User = user
        self.page = page
        self.user_profile = get_user_profile(user.id)
        perms = list(default_user_permissions.keys())
        perms = perms[((page-1)*10):(page*10)]
        for perm in perms:
            perm_styled = perm.replace("_", " ").title()
            try:
                permission = self.user_profile["permissions"][perm]
            except:
                self.user_profile["permissions"][perm] = default_user_permissions[perm]
                save_user_profile(user)
                permission = default_user_permissions[perm]
            if permission:
                buttonstyle = discord.ButtonStyle.success
            else:
                buttonstyle = discord.ButtonStyle.danger
            button = discord.ui.Button(label = perm_styled, style=buttonstyle, custom_id=perm)
            button.callback = self.open_modal_button_callback
            self.add_item(button)
        self.max_page = math.ceil(len(default_user_permissions.keys())/10)

        config.page_select_buttons(self, page)
    async def page_selector(self, interaction: discord.Interaction):
        if not await permission_check(interaction.user, "edit_permissions"): return await interaction.response.send_message(":warning: No permission.",ephemeral=True)
        await config.select_page(interaction, self.old_interaction, self.page, self.max_page, PermissionPanel)

    async def open_modal_button_callback(self, interaction: discord.Interaction):
        if not await permission_check(interaction.user, "edit_permissions"): return await interaction.response.send_message(":warning: No permission.",ephemeral=True)
        await interaction.response.defer(ephemeral=True, thinking=False)
        perm = interaction.data["custom_id"]
        self.user_profile["permissions"][perm] = not self.user_profile["permissions"][perm]
        save_user_profile(self.user_profile)
        await self.old_interaction.edit_original_response(view=PermissionPanel(self.old_interaction, self.user))