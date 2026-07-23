import discord, typing
from discord import app_commands
from discord.ext import commands
from utils.bot import bot
from utils import users, config, jsonIO, db
from api import gui

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Permissions(bot=bot))

class Permissions(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    permissions = app_commands.Group(name="permissions", description=".")

    @permissions.command(name="default", description="Manage default permissions")
    async def default(self, interaction: discord.Interaction):
        if not await users.permission_check(interaction.user.id, "edit_permissions"):
            return await interaction.response.send_message(":warning: No permission.", ephemeral=True)
        await interaction.response.send_message(view=DefaultPermissionPanel(interaction.guild.id))

    @permissions.command(name="user", description="Configure user permissions")
    async def user(self, interaction: discord.Interaction, target: typing.Optional[discord.Member]):
        if not await users.permission_check(interaction.user.id, "edit_permissions"):
            return await interaction.response.send_message(":warning: No permission.", ephemeral=True)
        if target == None:
            target = interaction.user
        await interaction.response.send_message(content = f"Permissions for: {target.mention}",view=UserPermissionPanel(target))

    @permissions.command(name="roles", description="Configure role permissions")
    async def roles(self, interaction: discord.Interaction):
        if not await users.permission_check(interaction.user.id, "edit_permissions"):
            return await interaction.response.send_message(":warning: No permission.", ephemeral=True)
        await interaction.response.send_message(view=RolePanel())

colors = {
    False: discord.ButtonStyle.danger, # 4
    None: discord.ButtonStyle.primary, # 1
    True: discord.ButtonStyle.success  # 3
}

next_perm = {
    False: None,
    None: True,
    True: False
}

class DefaultPermissionPanel(gui.PageUI):
    def __init__(self, guild_id: int, page: int = 1):
        perms = db.get("server", (guild_id,), ("server_id",) ("perms",))
        perms = list(perms.keys())
        super().__init__(page=page, element_count=len(perms), data_transfer=guild_id)
        perms = perms[((self.page-1)*10):(self.page*10)]
        for perm in perms:
            permission = config.permissions_config[perm]["default_enabled"]
            button = discord.ui.Button(label = config.permissions_config[perm]["display_name"], style=colors[permission], custom_id=perm)
            button.callback = self.callback
            self.add_item(button)

    async def callback(self, interaction: discord.Interaction):
        if not await users.permission_check(interaction.user.id, "edit_permissions"):
            return await interaction.response.send_message(":warning: No permission.", ephemeral=True)
        perm = interaction.data["custom_id"]
        if config.permissions_config[perm]["toggleable"] or interaction.user.id in config.server_config["bot_admins"]:
            config.permissions_config[perm]["default_enabled"] = not config.permissions_config[perm]["default_enabled"]
            config.save_permisions_config()
        else:
            return await interaction.response.send_message("Permission can only be toggled by bot admins", ephemeral=True)
        await interaction.response.defer(ephemeral=True, thinking=False)
        await interaction.message.edit(view=DefaultPermissionPanel())

class UserPermissionPanel(gui.PageUI):
    def __init__(self, user: discord.Member, page: int = 1):
        perms = list(config.permissions_config.keys())
        super().__init__(data_transfer=user, page=page, element_count=len(perms))
        self.user: discord.User = user
        self.user_profile = users.get_user(user.id)
        self.user_permissions = self.user_profile[1]

        perms = perms[((self.page-1)*10):(self.page*10)]
        for perm in perms:
            try:
                permission = self.user_permissions[perm]
            except:
                self.user_profile = users.permissions(self.user_profile)
                permission = self.user_permissions[perm]
            button = discord.ui.Button(label = config.permissions_config[perm]["display_name"], style=colors[permission], custom_id=perm)
            button.callback = self.callback
            self.add_item(button)

    async def callback(self, interaction: discord.Interaction):
        if not await users.permission_check(interaction.user.id, "edit_permissions"):
            return await interaction.response.send_message(":warning: No permission.", ephemeral=True)
        perm = interaction.data["custom_id"]
        if config.permissions_config[perm]["toggleable"] or interaction.user.id in config.server_config["bot_admins"]:
            self.user_permissions[perm] = next_perm[self.user_permissions[perm]]
            users.save_user_profile(self.user_profile)
        else:
            return await interaction.response.send_message("Permission can only be toggled by bot admins", ephemeral=True)
        await interaction.response.defer(ephemeral=True, thinking=False)
        await interaction.message.edit(view=UserPermissionPanel(self.user))

class RolePanel(gui.PageUI):
    def __init__(self, _ = None, page: int = 1):
        roles = [[role.id, role.name] for role in bot.guilds[0].roles]
        super().__init__(page=page, element_count=len(roles))

        roles = roles[((self.page-1)*10):(self.page*10)]
        for role in roles:
            button = discord.ui.Button(label=role[1], style=discord.ButtonStyle.blurple, custom_id=str(role[0]))
            button.callback = self.callback
            self.add_item(button)

    async def callback(self, interaction: discord.Interaction):
        if not await users.permission_check(interaction.user.id, "edit_permissions"):
            return await interaction.response.send_message(":warning: No permission.", ephemeral=True)
        await interaction.response.defer(ephemeral=True, thinking=False)
        role = int(interaction.data["custom_id"])
        role = bot.guilds[0].get_role(role)
        users.update_role(role.id)
        view = RolePermissionPanel(role.id)
        await interaction.message.edit(content=f"Permissions for {role.mention}:", view=view)

class RolePermissionPanel(gui.PageUI):
    def __init__(self, data_transfer: int, page: int = 1):
        perms = list(config.permissions_config.keys())
        super().__init__(data_transfer=data_transfer, page=page, element_count=len(perms))
        role, = db.get("role", data_transfer, "perms")
        self.role = role
        perms = perms[((self.page-1)*10):(self.page*10)]
        for perm in perms:
            button = discord.ui.Button(label=config.permissions_config[perm]["display_name"], style=colors[role[perm]], custom_id=str(perm))
            button.callback = self.callback
            self.add_item(button)

        button = discord.ui.Button(label="Back", style=discord.ButtonStyle.gray, custom_id="back", row=4)
        button.callback = self.back
        self.add_item(button)

    async def back(self, interaction: discord.Interaction):
        if not await users.permission_check(interaction.user.id, "edit_permissions"):
            return await interaction.response.send_message(":warning: No permission.", ephemeral=True)
        await interaction.response.defer(ephemeral=True, thinking=False)
        await interaction.message.edit(content="", view=RolePanel())

    async def callback(self, interaction: discord.Interaction):
        if not await users.permission_check(interaction.user.id, "edit_permissions"):
            return await interaction.response.send_message(":warning: No permission.", ephemeral=True)

        perm = interaction.data["custom_id"]
        if config.permissions_config[perm]["toggleable"] or interaction.user.id in config.server_config["bot_admins"]:
            self.role[perm] = next_perm[self.role[perm]]
        else:
            return await interaction.response.send_message("Permission can only be toggled by bot admins", ephemeral=True)
        db.insert("role", ("id", "perms"), (self.data_transfer, jsonIO.dumps(self.role)))
        view = RolePermissionPanel(self.data_transfer)
        await interaction.response.defer(ephemeral=True, thinking=False)
        await interaction.message.edit(view=view)
