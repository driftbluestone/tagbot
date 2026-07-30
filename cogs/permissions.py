import discord, typing
from discord import app_commands
from discord.ext import commands
from utils import utils
from db import db, permission, server, users
from api import gui

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Permissions(bot=bot))

class Permissions(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    class PermissionCommands(app_commands.Group):
        async def interaction_check(self, interaction: discord.Interaction):
            permission = await users.check_permission(interaction.guild.id, interaction.user.id, "#:edit_permissions")
            if not permission:
                await interaction.response.send_message(":warning: No permission", ephemeral=True)
            return permission

    permissions = PermissionCommands(name="permissions", description=".")

    @permissions.command(name="default", description="Manage default permissions")
    async def default(self, interaction: discord.Interaction):
        await interaction.response.send_message(view=DefaultPermissionPanel(interaction.guild.id))

    @permissions.command(name="user", description="Configure user permissions")
    async def user(self, interaction: discord.Interaction, target: typing.Optional[discord.Member]):
        if target == None:
            target = interaction.user
        await interaction.response.send_message(content = f"Permissions for: {target.mention}",view=UserPermissionPanel(target))

    @permissions.command(name="roles", description="Configure role permissions")
    async def roles(self, interaction: discord.Interaction):
        await interaction.response.send_message(view=RolePanel(interaction.guild))

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
        self.perm_values = server.perms(guild_id)
        perms = list(self.perm_values.keys())
        super().__init__(page=page, element_count=len(perms), data_transfer=guild_id)
        perms = perms[((self.page-1)*10):(self.page*10)]
        
        for perm in perms:
            value = self.perm_values[perm]
            perm = permission.get(perm)
            button = discord.ui.Button(label = perm["display_name"], style=colors[value], custom_id=perm["name"])
            button.callback = self.callback
            self.add_item(button)

    async def callback(self, interaction: discord.Interaction):
        if not await users.check_permission(interaction.guild.id, interaction.user.id, "#:edit_permissions"):
            return await interaction.response.send_message(":warning: No permission.", ephemeral=True)
        name = interaction.data["custom_id"]
        perm = permission.get(name)
        if not (perm["toggleable"]) and not (interaction.user.id in utils.bot_config["bot_admins"] or interaction.user.guild_permissions.administrator):
            return await interaction.response.send_message("Permission can only be toggled by admins", ephemeral=True)
        permission.set(interaction.guild.id, 0, name, not self.perm_values[name])
        await interaction.response.defer(ephemeral=True, thinking=False)
        await interaction.message.edit(view=DefaultPermissionPanel(self.data_transfer))

class UserPermissionPanel(gui.PageUI):
    def __init__(self, member: discord.Member, page: int = 1):
        perms = list(server.perms(member.guild.id))
        
        super().__init__(data_transfer=member, page=page, element_count=len(perms))
        self.user: discord.Member = member
        self.user_perms = users.perms(member.guild.id, member.id)
        perms = perms[((self.page-1)*10):(self.page*10)]
        for perm in perms:
            if perm not in self.user_perms:
                value = None
            else:
                value = self.user_perms[perm]
            display_name = permission.get(perm)["display_name"]
            button = discord.ui.Button(label=display_name, style=colors[value], custom_id=perm)
            button.callback = self.callback
            self.add_item(button)

    async def callback(self, interaction: discord.Interaction):
        if not await users.check_permission(interaction.guild.id, interaction.user.id, "#:edit_permissions"):
            return await interaction.response.send_message(":warning: No permission.", ephemeral=True)
        name = interaction.data["custom_id"]
        perm = permission.get(name)
        if not (perm["toggleable"]) and not (interaction.user.id in utils.bot_config["bot_admins"] or interaction.user.guild_permissions.administrator):
            return await interaction.response.send_message("Permission can only be toggled by admins", ephemeral=True)
        next = next_perm[self.user_perms[name] if name in self.user_perms else None]
        if next is None:
            db.delete("permissions", ("server_id", "permission", "id"), (interaction.guild.id, name, self.user.id))
        else:
            users.save_permission(interaction.guild.id, self.user.id, name, next)
            
        await interaction.response.defer(ephemeral=True, thinking=False)
        await interaction.message.edit(view=UserPermissionPanel(self.user, self.page))

class RolePanel(gui.PageUI):
    def __init__(self, guild: discord.Guild, page: int = 1):
        roles = [[role.id, role.name] for role in guild.roles]
        super().__init__(page=page, element_count=len(roles), data_transfer=guild)

        roles = roles[((self.page-1)*10):(self.page*10)]
        for role in roles:
            button = discord.ui.Button(label=role[1], style=discord.ButtonStyle.blurple, custom_id=str(role[0]))
            button.callback = self.callback
            self.add_item(button)

    async def callback(self, interaction: discord.Interaction):
        if not await users.check_permission(interaction.guild.id, interaction.user.id, "#:edit_permissions"):
            return await interaction.response.send_message(":warning: No permission.", ephemeral=True)
        await interaction.response.defer(ephemeral=True, thinking=False)
        role = int(interaction.data["custom_id"])
        view = RolePermissionPanel((self.data_transfer, role))
        await interaction.message.edit(content=f"Permissions for <@&{role}>:", view=view)

class RolePermissionPanel(gui.PageUI):
    def __init__(self, data_transfer: tuple[discord.Guild, int], page: int = 1):
        guild, role = data_transfer
        perms = list(server.perms(guild.id))
        super().__init__(data_transfer=data_transfer, page=page, element_count=len(perms))
        self.role = users.perms(guild.id, role)
        self.role_id = role
        perms = perms[((self.page-1)*10):(self.page*10)]
        for perm in perms:
            if perm not in self.role:
                color = None
            else:
                color = self.role[perm]
            perm = permission.get(perm)
            button = discord.ui.Button(label=perm["display_name"], style=colors[color], custom_id=perm["name"])
            button.callback = self.callback
            self.add_item(button)

        button = discord.ui.Button(label="Back", style=discord.ButtonStyle.gray, custom_id="back", row=4)
        button.callback = self.back
        self.add_item(button)

    async def back(self, interaction: discord.Interaction):
        if not await users.check_permission(interaction.guild.id, interaction.user.id, "#:edit_permissions"):
            return await interaction.response.send_message(":warning: No permission.", ephemeral=True)
        await interaction.response.defer(ephemeral=True, thinking=False)
        await interaction.message.edit(content="", view=RolePanel(interaction.guild))

    async def callback(self, interaction: discord.Interaction):
        if not await users.check_permission(interaction.guild.id, interaction.user.id, "#:edit_permissions"):
            return await interaction.response.send_message(":warning: No permission.", ephemeral=True)

        name = interaction.data["custom_id"]
        perm = permission.get(name)
        if not (perm["toggleable"]) and not (interaction.user.id in utils.bot_config["bot_admins"] or interaction.user.guild_permissions.administrator):
            return await interaction.response.send_message("Permission can only be toggled by admins", ephemeral=True)
        next = next_perm[self.role[name] if name in self.role else None]
        if next is None:
            db.delete("permissions", ("server_id", "permission", "id"), (interaction.guild.id, name, self.role_id))
        else:
            users.save_permission(interaction.guild.id, self.role_id, name, next)
        view = RolePermissionPanel(self.data_transfer)
        await interaction.response.defer(ephemeral=True, thinking=False)
        await interaction.message.edit(view=view)
