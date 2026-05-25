import discord, os, json
from api import gui
from modules.bot import bot
from utils import users
from utils import config
from pathlib import Path
DIR = Path(__file__).resolve().parent.parent

class UserPermissionPanel(gui.MenuGUI):
    def __init__(self, interaction: discord.Interaction, user: discord.Member, page: int = 1):
        perms = list(config.permissions_config.keys())
        super().__init__(interaction=interaction, interaction_permission="edit_permissions", data_transfer=user, page=page, element_count=len(perms))
        self.user: discord.User = user
        self.user_profile = users.get_user_profile(user.id)
        
        perms = perms[((self.page-1)*10):(self.page*10)]
        for perm in perms:
            perm_styled = perm.replace("_", " ").title()
            try:
                permission = self.user_profile["permissions"][perm]
            except:
                self.user_profile["permissions"][perm] = False
                if config.permissions_config[perm] == None:
                    self.user_profile["permissions"][perm] = True
                users.save_user_profile(self.user_profile)
                permission = self.user_profile["permissions"][perm]
            if permission:
                buttonstyle = discord.ButtonStyle.success
            else:
                buttonstyle = discord.ButtonStyle.danger
            button = discord.ui.Button(label = perm_styled, style=buttonstyle, custom_id=perm)
            button.callback = self.callback
            self.add_item(button)

    async def callback(self, interaction: discord.Interaction):
        if not await users.permission_check(interaction.user.id, "edit_permissions"):
            return await interaction.response.send_message(":warning: No permission.", ephemeral=True)
        await interaction.response.defer(ephemeral=True, thinking=False)
        perm = interaction.data["custom_id"]
        self.user_profile["permissions"][perm] = not self.user_profile["permissions"][perm]
        users.save_user_profile(self.user_profile)
        await self.interaction.edit_original_response(view=UserPermissionPanel(self.interaction, self.user))

class RolePanel(gui.MenuGUI):
    def __init__(self, interaction: discord.Interaction, _ = None, page: int = 1):
        roles = [[role.id, role.name] for role in bot.guilds[0].roles]
        super().__init__(interaction=interaction, interaction_permission="edit_permissions", page=page, element_count=len(roles))

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
        view = RolePermissionPanel(self.interaction, role.id)
        await self.interaction.edit_original_response(view=view)

class RolePermissionPanel(gui.MenuGUI):
    def __init__(self, interaction: discord.Interaction, data_transfer: int, page: int = 1):
        perms = list(config.permissions_config.keys())
        super().__init__(interaction=interaction, interaction_permission="edit_permissions", data_transfer=data_transfer, page=page, element_count=len(perms))

        with open(f"{DIR}/data/roles/{data_transfer}", "r") as file:
            role = json.load(file)
        perms = perms[((self.page-1)*10):(self.page*10)]
        for perm in perms:
            buttonstyle = discord.ButtonStyle.success if role[perm] else discord.ButtonStyle.danger
            button = discord.ui.Button(label=perm, style=buttonstyle, custom_id=str(perm))
            button.callback = self.callback
            self.add_item(button)
        
        button = discord.ui.Button(label="Back", style=discord.ButtonStyle.gray, custom_id="back", row=4)
        button.callback = self.back
        self.add_item(button)
    
    async def back(self, interaction: discord.Interaction):
        if not await users.permission_check(interaction.user.id, "edit_permissions"):
            return await interaction.response.send_message(":warning: No permission.", ephemeral=True)
        await interaction.response.defer(ephemeral=True, thinking=False)
        view = RolePanel(self.interaction)
        await self.interaction.edit_original_response(view=view)
    
    async def callback(self, interaction: discord.Interaction):
        if not await users.permission_check(interaction.user.id, "edit_permissions"):
            return await interaction.response.send_message(":warning: No permission.", ephemeral=True)
        await interaction.response.defer(ephemeral=True, thinking=False)
        perm = interaction.data["custom_id"]
        filepath = f"{DIR}/data/roles/{self.data_transfer}"
        with open(filepath, "r") as file:
            role = json.load(file)
        role[perm] = not role[perm]
        with open(filepath, "w") as file:
                json.dump(role, file, indent=2)
        view = RolePermissionPanel(self.interaction, self.data_transfer)
        await self.interaction.edit_original_response(view=view)