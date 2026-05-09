import discord, json
from api import gui
from utils.users import get_user_profile, permission_check, save_user_profile
from pathlib import Path
DIR = Path(__file__).resolve().parent.parent

class PermissionPanel(gui.MenuGUI):
    def __init__(self, interaction: discord.Interaction, user: discord.User, page: int = 1):
        with open(f"{DIR}/data/static/permissions.json", "r") as file:
            user_permission_equivalent = json.load(file)
        perms = list(user_permission_equivalent.keys())
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
                if user_permission_equivalent[perm] == None:
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
