import discord
import re
from modules import config
from modules.config import server_config, save_server_config
from modules.tags import users

EMOJI = re.compile(
    "["
    "\U0001F600-\U0001F64F"  # Emoticons
    "\U0001F300-\U0001F5FF"  # Miscellaneous Symbols and Pictographs
    "\U0001F680-\U0001F6FF"  # Transport and Map Symbols
    "\U0001F700-\U0001F77F"  # Alchemical Symbols
    "]", flags=re.UNICODE
)

class BoardMaster(discord.ui.View):
    def __init__(self, old_interaction):
        super().__init__(timeout=1000000000)
        self.old_interaction: discord.Interaction = old_interaction
        boards = list(server_config["boards"].keys())
        for board in boards:
            buttonstyle = discord.ButtonStyle.primary
            button = discord.ui.Button(emoji=board, style=buttonstyle, custom_id=board)
            button.callback = self.open_modal_button_callback
            self.add_item(button)
        if len(server_config["boards"].keys()) < 10:
            button = discord.ui.Button(label="New Board", custom_id="new", row=4)
            button.callback = self.new_group
            self.add_item(button)
    # function that is run when button is pressed
    async def open_modal_button_callback(self, interaction: discord.Interaction):
        if not await users.permission_check(interaction.user, "manage_boards"): return await interaction.response.send_message(":warning: No permission.",ephemeral=True)
        board = interaction.data["custom_id"]
        old_interaction = self.old_interaction

        view = Board(old_interaction, board)
        content = f"Channel: <#{server_config["boards"][board][0]}>"
        if server_config["boards"][board][0] == 0:
            content = f"Channel: None"
        await old_interaction.edit_original_response(content=content, view=view)
        await interaction.response.defer(ephemeral=True, thinking=False)

    async def new_group(self, interaction: discord.Interaction):
        if not await users.permission_check(interaction.user, "manage_boards"): return await interaction.response.send_message(":warning: No permission.",ephemeral=True)
        return await interaction.response.send_modal(NewBoard(self.old_interaction))

class NewBoard(discord.ui.Modal, title="Create New Board"):
    def __init__(self, old_interaction):
        super().__init__()
        self.old_interaction = old_interaction
        self.user_input = discord.ui.TextInput(
            label=f"Enter emoji",
            placeholder="Using the copy message content feature is recommended.",
            style=discord.TextStyle.short,
            required=True
        )
        self.add_item(self.user_input)
    
    async def on_submit(self, interaction: discord.Interaction):
        value = self.user_input.value
        
        old_interaction = self.old_interaction
        
        try:
            emoji_id = re.sub("\:.+\:", "", value[1:-1])
            emoji = await interaction.guild.fetch_emoji(emoji_id)
        except:
            emoji = bool(EMOJI.match(value))

        if emoji == False:
            return await interaction.response.send_message("Please enter a valid emoji.", ephemeral=True)
        if value in server_config["boards"].keys():
            return await interaction.response.send_message("Name already in use.", ephemeral=True)
        if emoji == False:
            value = f"<:{emoji.name}:{emoji.id}>"

        server_config["boards"][value] = [0, 10]
        await save_server_config()
        content = f"Channel: None"
        view = Board(old_interaction, value)
        await old_interaction.edit_original_response(content=content, view=view)
        return await interaction.response.defer(ephemeral=True, thinking=False)

class Board(discord.ui.View):
    def __init__(self, old_interaction, board):
        super().__init__(timeout=1000000000)
        self.old_interaction: discord.Interaction = old_interaction
        self.board = board

        button = discord.ui.Button(label = f"Threshold: {server_config["boards"][board][1]}", style=discord.ButtonStyle.primary, custom_id="threshold")
        button.callback = self.threshold
        self.add_item(button)
        button = discord.ui.Button(label = "Delete", style=discord.ButtonStyle.danger, custom_id="delete")
        button.callback = self.delete
        self.add_item(button)
        button = discord.ui.Button(label = "Back", style=discord.ButtonStyle.secondary, custom_id="back")
        button.callback = self.back
        self.add_item(button)
    
    @discord.ui.select(
        cls=discord.ui.ChannelSelect,
        placeholder="Select the channel...",
        channel_types=[discord.ChannelType.text],
        min_values=1,
        max_values=1
    )
    async def select_callback(self, interaction: discord.Interaction, select: discord.ui.ChannelSelect):
        if not await users.permission_check(interaction.user, "manage_boards"): return await interaction.response.send_message(":warning: No permission.",ephemeral=True)
        channel = select.values[0] 
        await interaction.response.defer(ephemeral=True, thinking=False)
        server_config["boards"][self.board][0] = channel.id
        content = f"Channel: <#{server_config["boards"][self.board][0]}>"
        if server_config["boards"][self.board][0] == 0:
            content = f"Channel: None"
        await self.old_interaction.edit_original_response(content=content)
        await save_server_config()
    
    async def threshold(self, interaction: discord.Interaction):
        if not await users.permission_check(interaction.user, "manage_boards"): return await interaction.response.send_message(":warning: No permission.",ephemeral=True)
        await interaction.response.send_modal(SetThreshold(self.old_interaction, self.board))
    async def delete(self, interaction: discord.Interaction):
        if not await users.permission_check(interaction.user, "manage_boards"): return await interaction.response.send_message(":warning: No permission.",ephemeral=True)
        server_config["boards"].pop(self.board)
        await save_server_config()
        await self.back(interaction)
    async def back(self, interaction: discord.Interaction):
        if not await users.permission_check(interaction.user, "manage_boards"): return await interaction.response.send_message(":warning: No permission.",ephemeral=True)
        old_interaction = self.old_interaction
        view = BoardMaster(old_interaction)

        await old_interaction.edit_original_response(content="", view=view)
        return await interaction.response.defer(ephemeral=True, thinking=False)
        
class SetThreshold(discord.ui.Modal, title="Set threshold"):
    def __init__(self, old_interaction, board):
        super().__init__()
        self.old_interaction = old_interaction
        self.board = board
        self.user_input = discord.ui.TextInput(
            label=f"How many emojis need to be reacted?",
            placeholder=f"Enter a number 1 or greater...",
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
        if value < 1:
            return await interaction.response.send_message(f"Input must be 1 or greater.",ephemeral=True)
        server_config["boards"][self.board][1] = value
        await save_server_config()
        view = Board(old_interaction, self.board)
        await old_interaction.edit_original_response(view=view)
        return await interaction.response.defer(ephemeral=True, thinking=False)