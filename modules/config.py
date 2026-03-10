import discord, json, pathlib, math
from modules.tags import users
DIR = pathlib.Path(__file__).resolve().parent
with open(f"{DIR}/../config.json", "r", encoding='utf-8') as file:
    server_config = json.load(file)

async def save_server_config():
    with open(f"{DIR}/../config.json", "w", encoding="utf-8") as file:
        json.dump(server_config, file, indent=2)

class ConfigButton(discord.ui.View):
    def __init__(self, old_interaction, _ = None, page = 1):
        super().__init__(timeout=1000000000)
        self.old_interaction: discord.Interaction = old_interaction
        self.page = page
        groups = list(server_config["logs"].keys())
        groups = groups[((page-1)*10):(page*10)]
        for logging_group in groups:
            buttonstyle = discord.ButtonStyle.primary
            button = discord.ui.Button(label = logging_group, style=buttonstyle, custom_id=logging_group)
            button.callback = self.open_modal_button_callback
            self.add_item(button)
        self.max_page = math.ceil(len(server_config["logs"].keys())/10)
        button = discord.ui.Button(label="New Group", custom_id="new", row=4)
        button.callback = self.new_group
        self.add_item(button)
        page_select_buttons(self, page)
    # function that is run when button is pressed
    async def open_modal_button_callback(self, interaction: discord.Interaction):
        if not await users.permission_check(interaction.user, "log_admin"): return await interaction.response.send_message(":warning: No permission.",ephemeral=True)
        group = interaction.data["custom_id"]
        old_interaction = self.old_interaction

        view = ConfigSubButton(old_interaction, group, self.page)
        if server_config["logs"][group][0] == 0:
            content = "Channel: None"
        else:
            content = f"Channel: <#{server_config["logs"][group][0]}>"
        await old_interaction.edit_original_response(content=content, view=view)
        await interaction.response.defer(ephemeral=True, thinking=False)

    async def page_selector(self, interaction: discord.Interaction):
        if not await users.permission_check(interaction.user, "log_admin"): return await interaction.response.send_message(":warning: No permission.",ephemeral=True)
        await select_page(interaction, self.old_interaction, self.page, self.max_page, ConfigButton)
    async def new_group(self, interaction: discord.Interaction):
        if not await users.permission_check(interaction.user, "log_admin"): return await interaction.response.send_message(":warning: No permission.",ephemeral=True)
        return await interaction.response.send_modal(NewLogGroup(self.old_interaction))
            
class ConfigSubButton(discord.ui.View):
    def __init__(self, old_interaction, group, page = 1):
        super().__init__(timeout=1000000000)
        self.group = group
        self.page = page
        self.old_interaction: discord.Interaction = old_interaction
        self.max_page = math.ceil(len(server_config["logs"][group][1:])/10)
        buttonstyle = discord.ButtonStyle.primary
        logs = server_config["logs"][group][1:][((page-1)*10):(page*10)]
        for log in logs:
            log_formatted = log.replace("_", " ").title()
            button = discord.ui.Button(label = log_formatted, style=buttonstyle, custom_id=log)
            button.callback = self.open_modal_button_callback
            self.add_item(button)
        
        button = discord.ui.Button(label = "New Action", custom_id="new", row=4)
        button.callback = self.new_action
        self.add_item(button)
        button = discord.ui.Button(label = "Delete Group", custom_id="del", row=4)
        button.callback = self.delete
        self.add_item(button)
        button = discord.ui.Button(label = "Back", custom_id="back", row=4)
        button.callback = self.back
        self.add_item(button)

        page_select_buttons(self, page)
    async def page_selector(self, interaction: discord.Interaction):
        if not await users.permission_check(interaction.user, "log_admin"): return await interaction.response.send_message(":warning: No permission.",ephemeral=True)
        await select_page(interaction, self.old_interaction, self.page, self.max_page, ConfigSubButton, self.group)

    @discord.ui.select(
        cls=discord.ui.ChannelSelect,
        placeholder="Select the channel...",
        channel_types=[discord.ChannelType.text],
        min_values=1,
        max_values=1
    )
    async def select_callback(self, interaction: discord.Interaction, select: discord.ui.ChannelSelect):
        if not await users.permission_check(interaction.user, "log_admin"): return await interaction.response.send_message(":warning: No permission.",ephemeral=True)
        channel = select.values[0] 
        await interaction.response.defer(ephemeral=True, thinking=False)
        server_config["logs"][self.group][0] = channel.id
        for log in server_config["logs"][self.group][1:]:
            server_config["logged_actions"][log] = channel.id
        content = f"Channel: <#{server_config["logs"][self.group][0]}>"
        await self.old_interaction.edit_original_response(content=content)
        await save_server_config()

    async def open_modal_button_callback(self, interaction: discord.Interaction):
        if not await users.permission_check(interaction.user, "log_admin"): return await interaction.response.send_message(":warning: No permission.",ephemeral=True)
        old_interaction = self.old_interaction
        log = interaction.data["custom_id"]
        server_config["logs"][self.group].remove(log)
        server_config["logged_actions"].pop(log)
        server_config["unlogged_actions"].append(log)
        await save_server_config()
        
        view = ConfigSubButton(old_interaction, self.group)
        if server_config["logs"][self.group][0] == 0:
            content = "Channel: None"
        else:
            content = f"Channel: <#{server_config["logs"][self.group][0]}>"
        await old_interaction.edit_original_response(content=content, view=view)
        await interaction.response.defer(ephemeral=True, thinking=False)
    
    async def back(self, interaction: discord.Interaction):
        if not await users.permission_check(interaction.user, "log_admin"): return await interaction.response.send_message(":warning: No permission.",ephemeral=True)
        view = ConfigButton(self.old_interaction, self.page)
        await self.old_interaction.edit_original_response(content="", view=view)
        await interaction.response.defer(ephemeral=True, thinking=False)

    async def new_action(self, interaction: discord.Interaction):
        if not await users.permission_check(interaction.user, "log_admin"): return await interaction.response.send_message(":warning: No permission.",ephemeral=True)
        view = NewAction(self.old_interaction, self.group)
        await self.old_interaction.edit_original_response(content="", view=view)
        await interaction.response.defer(ephemeral=True, thinking=False)
    
    async def delete(self, interaction):
        if not await users.permission_check(interaction.user, "log_admin"): return await interaction.response.send_message(":warning: No permission.",ephemeral=True)
        view = DeleteConfirm(self.old_interaction, self.group, self.page)
        await self.old_interaction.edit_original_response(content="Are you sure?",view=view)
        await interaction.response.defer(ephemeral=True, thinking=False)

class NewLogGroup(discord.ui.Modal, title="Create new group"):
    def __init__(self, old_interaction):
        super().__init__()
        self.old_interaction = old_interaction
        self.user_input = discord.ui.TextInput(
            label=f"Enter group name",
            placeholder="",
            style=discord.TextStyle.short,
            required=True
        )
        self.add_item(self.user_input)
    
    async def on_submit(self, interaction: discord.Interaction):
        value = self.user_input.value
        old_interaction = self.old_interaction
        if value in ["new", "page1", "back1", "select", "next1", "last"]:
            return await interaction.response.send_message("Sorry, that name is reserved.", ephemeral=True)
        if value in server_config["logs"].keys():
            return await interaction.response.send_message("Name already in use.", ephemeral=True)
        server_config["logs"][value] = [0]
        await save_server_config()
        view = ConfigSubButton(old_interaction, value)
        await old_interaction.edit_original_response(content="", view=view)
        return await interaction.response.defer(ephemeral=True, thinking=False)

class DeleteConfirm(discord.ui.View):
    def __init__(self, old_interaction, group, page):
        super().__init__(timeout=1000000000)
        self.old_interaction = old_interaction
        self.group = group
        self.page = page
        button = discord.ui.Button(label="Yes", style=discord.ButtonStyle.success, custom_id="yes")
        button.callback = self.confirmation
        self.add_item(button)
        button = discord.ui.Button(label="No", style=discord.ButtonStyle.danger, custom_id="no")
        button.callback = self.back
        self.add_item(button)
    async def confirmation(self, interaction):
        if not await users.permission_check(interaction.user, "log_admin"): return await interaction.response.send_message(":warning: No permission.",ephemeral=True)
        for action in server_config["logs"][self.group][1:]:
            server_config["unlogged_actions"].append(action)
            server_config["logged_actions"].pop(action)
        server_config["logs"].pop(self.group)
        await save_server_config()
        view = ConfigButton(self.old_interaction, self.page)
        await self.old_interaction.edit_original_response(content="", view=view)
        await interaction.response.defer(ephemeral=True, thinking=False)
    async def back(self, interaction):
        if not await users.permission_check(interaction.user, "log_admin"): return await interaction.response.send_message(":warning: No permission.",ephemeral=True)
        view = ConfigSubButton(self.old_interaction, self.group, self.page)
        if server_config["logs"][self.group][0] == 0:
            content = "Channel: None"
        else:
            content = f"Channel: <#{server_config["logs"][self.group][0]}>"
        await self.old_interaction.edit_original_response(content=content, view=view)
        await interaction.response.defer(ephemeral=True, thinking=False)

class NewAction(discord.ui.View):
    def __init__(self, old_interaction, group, page = 1):
        super().__init__(timeout=1000000000)
        self.old_interaction: discord.Interaction = old_interaction
        self.page = page
        self.group = group
        actions = server_config["unlogged_actions"]
        actions = actions[((page-1)*10):(page*10)]
        for action in actions:
            action_styled = action.replace("_", " ").title()
            buttonstyle = discord.ButtonStyle.primary
            button = discord.ui.Button(label = action_styled, style=buttonstyle, custom_id=action)
            button.callback = self.open_modal_button_callback
            self.add_item(button)
        self.max_page = math.ceil(len(server_config["unlogged_actions"])/10)
        button = discord.ui.Button(label = "Back", custom_id="back", row=4)
        button.callback = self.back
        self.add_item(button)
        page_select_buttons(self, page)

    async def page_selector(self, interaction: discord.Interaction):
        if not await users.permission_check(interaction.user, "log_admin"): return await interaction.response.send_message(":warning: No permission.",ephemeral=True)
        await select_page(interaction, self.old_interaction, self.page, self.max_page, NewAction, self.group)

    async def open_modal_button_callback(self, interaction: discord.Interaction):
        if not await users.permission_check(interaction.user, "log_admin"): return await interaction.response.send_message(":warning: No permission.",ephemeral=True)
        action = interaction.data["custom_id"]
        
        server_config["unlogged_actions"].remove(action)
        server_config["logged_actions"][action] = server_config["logs"][self.group][0]
        server_config["logs"][self.group].append(action)
        await save_server_config()
        await self.back(interaction)
        
    async def back(self, interaction):
        await interaction.response.defer(ephemeral=True, thinking=False)
        view = ConfigSubButton(self.old_interaction, self.group)
        if server_config["logs"][self.group][0] == 0:
            content = "Channel: None"
        else:
            content = f"Channel: <#{server_config["logs"][self.group][0]}>"
        await self.old_interaction.edit_original_response(content=content, view=view)

async def select_page(interaction, old_interaction, page, max_page, return_view, group = None):
    config = interaction.data["custom_id"]
    
    if config == "select": return await interaction.response.send_modal(PageSelect(old_interaction, max_page, return_view, group))
    elif config == "page1": page = 1
    elif config == "back1": page-=1
    elif config == "next1": page+=1
    elif config == "last": page = max_page 
    content = ""
    view = return_view(old_interaction, group, page)
    if isinstance(return_view, ConfigSubButton):
        if server_config["logs"][group][0] == 0: content = "Channel: None"
        else: content = f"Channel: <#{server_config["logs"][group][0]}>"

    await old_interaction.edit_original_response(content=content, view=view)
    return await interaction.response.defer(ephemeral=True, thinking=False)

def page_select_buttons(self, page):
    if page != 1:
        button = discord.ui.Button(label="<<", custom_id="page1", row=3)
        button.callback = self.page_selector
        self.add_item(button)
        button = discord.ui.Button(label="<", custom_id="back1", row=3)
        button.callback = self.page_selector
        self.add_item(button)
    if self.max_page > 1:
        button = discord.ui.Button(label=page, custom_id="select", row=3)
        button.callback = self.page_selector
        self.add_item(button)
    if page != self.max_page and self.max_page != 0:
        button = discord.ui.Button(label=">", custom_id="next1", row=3)
        button.callback = self.page_selector
        self.add_item(button)
        button = discord.ui.Button(label=">>", custom_id="last", row=3)
        button.callback = self.page_selector
        self.add_item(button)

class PageSelect(discord.ui.Modal, title="Go to page"):
    def __init__(self, old_interaction, max_page, return_view, group = None):
        super().__init__()
        self.old_interaction = old_interaction
        self.max_page = max_page
        self.return_view = return_view
        self.group = group
        self.user_input = discord.ui.TextInput(
            label=f"Enter page",
            placeholder=f"Enter a number between 1 and {max_page}.",
            style=discord.TextStyle.short,
            required=True,
            max_length=10
        )
        self.add_item(self.user_input)
    
    async def on_submit(self, interaction: discord.Interaction):
        value = self.user_input.value
        old_interaction = self.old_interaction
        try: value = int(value)
        except: return await interaction.response.send_message("Error. Must input an integer.",ephemeral=True)
        if value < 1 or value > self.max_page:
            return await interaction.response.send_message(f"Page must be between 1 and {self.max_page}.",ephemeral=True)
        content = ""
        view = self.return_view(old_interaction, self.group, self.page)
        if isinstance(self.return_view, ConfigSubButton):
            if server_config["logs"][self.group][0] == 0: content = "Channel: None"
            else: content = f"Channel: <#{server_config["logs"][self.group][0]}>"

        await old_interaction.edit_original_response(content=content, view=view)

        await old_interaction.edit_original_response(content=content, view=view)
        return await interaction.response.defer(ephemeral=True, thinking=False)