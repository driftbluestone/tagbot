import discord, os
from api import gui
from modules.bot import bot
from utils.users import get_user_profile, permission_check, save_user_profile
from utils import config
from pathlib import Path
DIR = Path(__file__).resolve().parent.parent

class UserPermissionPanel(gui.MenuGUI):
    def __init__(self, interaction: discord.Interaction, user: discord.Member, page: int = 1):
        perms = list(config.permissions_config.keys())
        super().__init__(interaction=interaction, interaction_permission="edit_permissions", data_transfer=user, page=page, element_count=len(perms))
        self.user: discord.User = user
        self.user_profile = get_user_profile(user.id)
        
        perms = perms[((self.page-1)*10):(self.page*10)]
        for perm in perms:
            perm_styled = perm.replace("_", " ").title()
            try:
                permission = self.user_profile["permissions"][perm]
            except:
                self.user_profile["permissions"][perm] = False
                if config.permissions_config[perm] == None:
                    self.user_profile["permissions"][perm] = True
                save_user_profile(self.user_profile)
                permission = self.user_profile["permissions"][perm]
            if permission:
                buttonstyle = discord.ButtonStyle.success
            else:
                buttonstyle = discord.ButtonStyle.danger
            button = discord.ui.Button(label = perm_styled, style=buttonstyle, custom_id=perm)
            button.callback = self.callback
            self.add_item(button)

    async def callback(self, interaction: discord.Interaction):
        if not await permission_check(interaction.user.id, "edit_permissions"):
            return await interaction.response.send_message(":warning: No permission.", ephemeral=True)
        await interaction.response.defer(ephemeral=True, thinking=False)
        perm = interaction.data["custom_id"]
        self.user_profile["permissions"][perm] = not self.user_profile["permissions"][perm]
        save_user_profile(self.user_profile)
        await self.interaction.edit_original_response(view=UserPermissionPanel(self.interaction, self.user))

class RolePanel(gui.MenuGUI):
    def __init__(self, interaction: discord.Interaction, _ = None, page: int = 1):
        roles = [[role.id, role.name] for role in bot.guilds[0].roles]
        super().__init__(interaction=interaction, interaction_permission="edit_permissions", page=page, element_count=len(roles))

        roles = roles[((self.page-1)*10):(self.page*10)]
        for role in roles:
            button = discord.ui.Button(label=role[1], style=discord.ButtonStyle.blurple, custom_id=role[0])
            button.callback = self.callback
            self.add_item(button)
        
    async def callback(self, interaction: discord.Interaction):
        if not await permission_check(interaction.user.id, "edit_permissions"):
            return await interaction.response.send_message(":warning: No permission.", ephemeral=True)
        interaction.response.defer(ephemeral=True, thinking=False)
        role = interaction.data["custom_id"]
        role = bot.guilds[0].get_role(role)
        if not os.path.exists(f"{DIR}/data/roles/{role.id}"):
            self.create_role(role.id)
        view = RolePermissionPanel(self.interaction, self.page)
        self.interaction.edit_original_response(view=view)
    
    def create_role(role_id: int):
        pass

class RolePermissionPanel(gui.MenuGUI):
    def __init__(self, interaction: discord.Interaction, data_transfer: int, page: int = 1):
        perms = list(config.permissions_config.keys())
        super().__init__(interaction=interaction, interaction_permission="edit_permissions", data_transfer=data_transfer, page=page, element_count=len(perms))

        perms = perms[((self.page-1)*10):(self.page*10)]

        button = discord.ui.Button(label="Back", style=discord.ButtonStyle.gray, custom_id="back", row=4)
        button.callback = self.back
        self.add_item(button)
    
    async def back(self, interaction: discord.Interaction):
        if not await permission_check(interaction.user.id, "edit_permissions"):
            return await interaction.response.send_message(":warning: No permission.", ephemeral=True)
        interaction.response.defer(ephemeral=True, thinking=False)
        view = RolePanel(self.interaction, self.data_transfer)
        self.interaction.edit_original_response(view=view)