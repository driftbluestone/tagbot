import discord, json
from api import gui
from modules.bot import bot
from utils import users
from utils import config
from pathlib import Path
DIR = Path(__file__).resolve().parent.parent

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

class DefaultPermissionPanel(gui.MenuGUI):
    def __init__(self, interaction: discord.Interaction, _ = None, page: int = 1):
        perms = list(config.permissions_config.keys())
        super().__init__(interaction=interaction, interaction_permission="edit_permissions", page=page, element_count=len(perms))
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
        await self.interaction.edit_original_response(view=DefaultPermissionPanel(self.interaction))

class UserPermissionPanel(gui.MenuGUI):
    def __init__(self, interaction: discord.Interaction, user: discord.Member, page: int = 1):
        perms = list(config.permissions_config.keys())
        super().__init__(interaction=interaction, interaction_permission="edit_permissions", data_transfer=user, page=page, element_count=len(perms))
        self.user: discord.User = user
        self.user_profile = users.get_user_profile(user.id)
        
        perms = perms[((self.page-1)*10):(self.page*10)]
        for perm in perms:
            try:
                permission = self.user_profile["permissions"][perm]
            except:
                self.user_profile = users.permissions(self.user_profile)
                permission = self.user_profile["permissions"][perm]
            button = discord.ui.Button(label = config.permissions_config[perm]["display_name"], style=colors[permission], custom_id=perm)
            button.callback = self.callback
            self.add_item(button)

    async def callback(self, interaction: discord.Interaction):
        if not await users.permission_check(interaction.user.id, "edit_permissions"):
            return await interaction.response.send_message(":warning: No permission.", ephemeral=True)
        perm = interaction.data["custom_id"]
        if config.permissions_config[perm]["toggleable"] or self.user_profile["id"] in config.server_config["bot_admins"]:
            self.user_profile["permissions"][perm] = next_perm[self.user_profile["permissions"][perm]]
            users.save_user_profile(self.user_profile)
        else:
            return await interaction.response.send_message("Permission can only be toggled by bot admins", ephemeral=True)
        await interaction.response.defer(ephemeral=True, thinking=False)
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
        await self.interaction.edit_original_response(content=f"Permissions for {role.mention}:", view=view)

class RolePermissionPanel(gui.MenuGUI):
    def __init__(self, interaction: discord.Interaction, data_transfer: int, page: int = 1):
        perms = list(config.permissions_config.keys())
        super().__init__(interaction=interaction, interaction_permission="edit_permissions", data_transfer=data_transfer, page=page, element_count=len(perms))

        with open(f"{DIR}/data/roles/{data_transfer}.json", "r") as file:
            role = json.load(file)
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
        view = RolePanel(self.interaction)
        await self.interaction.edit_original_response(content="", view=view)
    
    async def callback(self, interaction: discord.Interaction):
        if not await users.permission_check(interaction.user.id, "edit_permissions"):
            return await interaction.response.send_message(":warning: No permission.", ephemeral=True)
        
        perm = interaction.data["custom_id"]
        filepath = f"{DIR}/data/roles/{self.data_transfer}.json"
        with open(filepath, "r") as file:
            role = json.load(file)
        if config.permissions_config[perm]["toggleable"] or interaction.user.id in config.server_config["bot_admins"]:
            role[perm] = next_perm[role[perm]]
        else:
            return await interaction.response.send_message("Permission can only be toggled by bot admins", ephemeral=True)
        with open(filepath, "w") as file:
            json.dump(role, file, indent=2)
        view = RolePermissionPanel(self.interaction, self.data_transfer)
        await interaction.response.defer(ephemeral=True, thinking=False)
        await self.interaction.edit_original_response(view=view)