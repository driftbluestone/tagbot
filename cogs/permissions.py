import discord, typing
from discord import app_commands
from discord.ext import commands
from utils import users
from modules.permission_panels import DefaultPermissionPanel, UserPermissionPanel, RolePanel

class Permissions(commands.Cog):
    permissions = app_commands.Group(name="permissions", description=".")

    @permissions.command(name="default", description="Manage default permissions")
    async def default(self, interaction: discord.Interaction):
        if not await users.permission_check(interaction.user.id, "edit_permissions"):
            return await interaction.response.send_message(":warning: No permission.", ephemeral=True)
        await interaction.response.send_message(view=DefaultPermissionPanel(interaction))

    @permissions.command(name="user", description="Configure user permissions")
    async def user(self, interaction: discord.Interaction, target: typing.Optional[discord.Member]):
        if not await users.permission_check(interaction.user.id, "edit_permissions"):
            return await interaction.response.send_message(":warning: No permission.", ephemeral=True)
        if target == None:
            target = interaction.user
        await interaction.response.send_message(content = f"Permissions for: {target.mention}",view=UserPermissionPanel(interaction, target))
    
    @permissions.command(name="roles", description="Configure role permissions")
    async def roles(self, interaction: discord.Interaction):
        if not await users.permission_check(interaction.user.id, "edit_permissions"):
            return await interaction.response.send_message(":warning: No permission.", ephemeral=True)
        await interaction.response.send_message(view=RolePanel(interaction))
