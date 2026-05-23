import discord, json
from api import gui
from utils.users import get_user_profile, permission_check, save_user_profile
from utils import config
from pathlib import Path
DIR = Path(__file__).resolve().parent.parent

class PermissionPanel(gui.MenuGUI):
    def __init__(self, interaction: discord.Interaction, user: discord.Member, page: int = 1):
        perms = list(config.user_config.keys())
        super().__init__(interaction=interaction, data_transfer=user, page=page, element_count=len(perms))
        self.user: discord.User = user
        self.user_profile = get_user_profile(user.id)
        
        perms = perms[((self.page-1)*10):(self.page*10)]
        for perm in perms:
            perm_styled = perm.replace("_", " ").title()
            try:
                permission = self.user_profile["permissions"][perm]
            except:
                self.user_profile["permissions"][perm] = False
                if config.user_config[perm] == None:
                    self.user_profile["permissions"][perm] = True
                save_user_profile(self.user_profile)
                permission = self.user_profile["permissions"][perm]
            if permission:
                buttonstyle = discord.ButtonStyle.success
            else:
                buttonstyle = discord.ButtonStyle.danger
            button = discord.ui.Button(label = perm_styled, style=buttonstyle, custom_id=perm)
            button.callback = self.open_modal_button_callback
            self.add_item(button)

    async def open_modal_button_callback(self, interaction: discord.Interaction):
        if not await permission_check(interaction.user.id, "edit_permissions"):
            return await interaction.response.send_message(":warning: No permission.", ephemeral=True)
        await interaction.response.defer(ephemeral=True, thinking=False)
        perm = interaction.data["custom_id"]
        self.user_profile["permissions"][perm] = not self.user_profile["permissions"][perm]
        save_user_profile(self.user_profile)
        await self.interaction.edit_original_response(view=PermissionPanel(self.interaction, self.user))

class RolePanel(gui.MenuGUI):
    def __init__(self, interaction: discord.Interaction, role: discord.Role, page: int = 1):
        super().__init__(interaction=interaction, data_transfer=role, page=page)