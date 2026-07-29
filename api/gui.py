import discord, math
from utils import utils
from utils.utils import bot
from api import users

__all__ = ["create_message_embed", "PageUI"]

async def create_message_embed(link: str):
    link_list = link.split("/")[5:]
    channel = bot.get_channel(int(link_list[0]))
    if channel == None:
        return
    msg: discord.Message = await channel.fetch_message(int(link_list[1]))

    name = msg.author.name
    pfp = msg.author.avatar
    content = msg.content

    embed=discord.Embed(description=f"{content}\n\n[Jump to message]({link})", timestamp=msg.created_at)
    for i in msg.attachments:
        embed.set_image(url=i)
    for i in msg.embeds:
        if i.url.startswith("https://tenor"):
            continue
        embed.set_image(url=i.url)
    embed.set_author(name=name, icon_url=pfp)
    
    embed.set_footer(text=f"From #{msg.channel.name}")
    return embed

class PageUI(discord.ui.View):
    """
    This object must be inherited.
    
    This class implements page scrolling buttons in a discord View, the buttons are added on row 3,
    leaving 10 places above for elements, and space below for action buttons. (i.e. "Create")

    The following variables must be declared using `super().__init__()`:
    - element_count: number of elements in the gui
    - page: the current page

    The rest are not required, but have uses:
    - interaction_permission: the permission required to interact with the view
    - data_transfer: any information that must persist between page selects
    - text: any text displayed with the message
    - embed: an embed displayed with the message
    """
    def __init__(self, element_count: int, interaction_permission: str = None, data_transfer = None, text: str = None, embed: discord.Embed = None, page: int = 1):
        super().__init__(timeout=None)
        self.page = page
        self.max_page = math.ceil(element_count/10)
        self.interaction_permission = interaction_permission
        self.data_transfer = data_transfer
        self.text = text
        self.embed = embed
        self._page_select_buttons()

    def _page_select_buttons(self: PageUI):
        if self.page != 1:
            button = discord.ui.Button(label="<<", custom_id="page1", row=3)
            button.callback = self.page_selector
            self.add_item(button)
            button = discord.ui.Button(label="<", custom_id="back1", row=3)
            button.callback = self.page_selector
            self.add_item(button)
        if self.max_page > 1:
            button = discord.ui.Button(label=self.page, custom_id="select", row=3)
            button.callback = self.page_selector
            self.add_item(button)
        if self.page != self.max_page and self.max_page != 0:
            button = discord.ui.Button(label=">", custom_id="next1", row=3)
            button.callback = self.page_selector
            self.add_item(button)
            button = discord.ui.Button(label=">>", custom_id="last", row=3)
            button.callback = self.page_selector
            self.add_item(button)

    async def page_selector(self, interaction: discord.Interaction):
        if self.interaction_permission == "!":
            if interaction.user.id not in utils.bot_config["bot_admins"]:
                return await interaction.response.send_message(":warning: No permission.", ephemeral=True)
        if self.interaction_permission is not None:
            if not await users.has_permission(interaction.guild.id, interaction.user.id, self.interaction_permission):
                return await interaction.response.send_message(":warning: No permission.", ephemeral=True)
        
        config = interaction.data["custom_id"]
    
        if config == "select": return await interaction.response.send_modal(_PageSelect(self))
        elif config == "page1": self.page = 1
        elif config == "back1": self.page -=1
        elif config == "next1": self.page +=1
        elif config == "last": self.page = self.max_page 
        await interaction.response.defer(ephemeral=True, thinking=False)
        view = self.__class__(self.data_transfer, self.page)

        await interaction.message.edit(content=self.text, embed=self.embed, view=view)

class _PageSelect(discord.ui.Modal, title="Go to page"):
    def __init__(self, view: PageUI, message: discord.Message): 
        super().__init__()
        self.view = view
        self.message = message
        self.user_input = discord.ui.TextInput(
            label=f"Enter page",
            placeholder=f"Enter a number between 1 and {view.max_page}.",
            style=discord.TextStyle.short,
            required=True,
            max_length=10
        )
        self.add_item(self.user_input)
    
    async def on_submit(self, interaction: discord.Interaction):
        try:
            value = int(self.user_input.value)
        except:
            return await interaction.response.send_message("Error. Must input an integer.", ephemeral=True)
        if value < 1 or value > self.view.max_page:
            return await interaction.response.send_message(f"Page must be between 1 and {self.view.max_page}.", ephemeral=True)
        view = self.view.__class__(data_transfer = self.view.data_transfer, page = value)
        await self.message.edit(content=self.view.text, embed=self.view.embed, view=view)
        await interaction.response.defer(ephemeral=True, thinking=False)

class MenuGUI(discord.ui.View):
    """
    # DEPRICATED

    This object must be inherited.
    
    This class implements page scrolling buttons in a discord View, the buttons are added on row 3,
    leaving 10 places above for elements, and space below for action buttons.

    The following variables must be declared using super().__init__():
    - interaction: the discord interaction object that triggered the view being sent
    - element_count: number of elements in the gui
    - page: the current page

    The rest are not required, but have uses:
    - interaction_permission: the permission required to interact with the view
    - data_transfer: any information that must persist between page selects
    - text: any text displayed with the message
    - embed: an embed displayed with the message
    """
    def __init__(self, interaction: discord.Interaction, element_count: int, interaction_permission: str = None, data_transfer = None, text: str = None, embed: discord.Embed = None, page: int = 1):
        super().__init__(timeout=None)
        self.interaction: discord.Interaction = interaction
        self.page = page
        self.max_page = math.ceil(element_count/10)
        self.interaction_permission = interaction_permission
        self.data_transfer = data_transfer
        self.text = text
        self.embed = embed
        self._page_select_buttons()

    def _page_select_buttons(self: MenuGUI):
        if self.page != 1:
            button = discord.ui.Button(label="<<", custom_id="page1", row=3)
            button.callback = self.page_selector
            self.add_item(button)
            button = discord.ui.Button(label="<", custom_id="back1", row=3)
            button.callback = self.page_selector
            self.add_item(button)
        if self.max_page > 1:
            button = discord.ui.Button(label=self.page, custom_id="select", row=3)
            button.callback = self.page_selector
            self.add_item(button)
        if self.page != self.max_page and self.max_page != 0:
            button = discord.ui.Button(label=">", custom_id="next1", row=3)
            button.callback = self.page_selector
            self.add_item(button)
            button = discord.ui.Button(label=">>", custom_id="last", row=3)
            button.callback = self.page_selector
            self.add_item(button)

    async def page_selector(self: MenuGUI, interaction: discord.Interaction):
        if not await users.has_permission(interaction.user.id, self.interaction_permission):
            return await interaction.response.send_message(":warning: No permission.", ephemeral=True)
        
        config = interaction.data["custom_id"]
    
        if config == "select": return await interaction.response.send_modal(self._PageSelect(self))
        elif config == "page1": self.page = 1
        elif config == "back1": self.page-=1
        elif config == "next1": self.page+=1
        elif config == "last": self.page = self.max_page 
        await interaction.response.defer(ephemeral=True, thinking=False)
        view = self.__class__(self.interaction, self.data_transfer, self.page)

        await self.interaction.edit_original_response(content=self.text, embed=self.embed, view=view)

    class _PageSelect(discord.ui.Modal, title="Go to page"):
        def __init__(self, view: MenuGUI): 
            super().__init__()
            self.view = view
            self.user_input = discord.ui.TextInput(
                label=f"Enter page",
                placeholder=f"Enter a number between 1 and {view.max_page}.",
                style=discord.TextStyle.short,
                required=True,
                max_length=10
            )
            self.add_item(self.user_input)
        
        async def on_submit(self, interaction: discord.Interaction):
            try: value = int(self.user_input.value)
            except: return await interaction.response.send_message("Error. Must input an integer.",ephemeral=True)
            if value < 1 or value > self.view.max_page:
                return await interaction.response.send_message(f"Page must be between 1 and {self.view.max_page}.",ephemeral=True)

            view = self.view.__class__(interaction = self.view.interaction, data_transfer = self.view.data_transfer, page = value)

            await self.view.interaction.edit_original_response(content=self.view.text, embed=self.view.embed, view=view)
            await interaction.response.defer(ephemeral=True, thinking=False)