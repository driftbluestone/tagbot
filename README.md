# Sonny
This is the bot used in the [AstroGreg discord](https://discord.gg/dUaZeV6Drp)

## Features:
* Tags
* Edit & Delete message logging
* Audit log action logging
* Sed functionality
* Message link embedding
* Extension framework to easily add your own features
## Usage Guide
### Tags
* Use %t to look at tag information
* Code tags are any tag that start with ``` on the same line as %t add
* usage of %t admin or any subcommands requires either administrator permissions, or the tag_admin flag on your user profile to be enabled
* enabling tag_admin on a user profile is done via %t admin promote "user"
### Sed
* Usage: sed/old text/new text
* Supports regex matching
### Permissions
* Accessed by using the /permissions command
* Requires administrator permission or the edit permissions bot permission
* The optional user input field allows managing the permissions of other users
#### Bot admins
* Bot admins bypass all permission checks
* They are also the only people who can manage bot extensions, not even server administrators can
* Bot admins can only be created by adding the user id to the bot admins list in config.json
* NEVER give this permission to people you do not trust, this permission gives them access to download and execute arbitrary github repositories
### Logging
* Use /logging to view and change logging configuration
* Requires administrator permission or manage logs bot permission
* Logs are categorized into groups, where each group sends any tracked actions into a selected channel
### Boards
* Use /boards to view and change board configuration
* Requires the manage channels permission or the manage boards bot permission
* This is a highly configurable starboard-like system where the emoji, channel, and threshold can be configured
* Once a message has a number of reactions of the set emoji equal to the threshold, the message is forwarded into the board channel
### Extensions
* A system for adding to bot functionality without interfering with the core bot logic
* Extensions can *only* be managed by bot admins
* Using /extension-add requires that you paste a github link in, which will then install the extension from that repo
## Setup Guide
### Requirements
* Python 3.13+
* [discord.py](https://discordpy.readthedocs.io/en/stable/)
* [Levenshtein](https://rapidfuzz.github.io/Levenshtein/)
* [Docker](https://www.docker.com/)
* If docker is not installed, code tags will simply fail to run, it is not a hard requirement
### Bot setup
1. Create a new bot by clicking ["New Application"](https://discord.com/developers/applications/)
2. In the Installation tab, disable "User Install"
3. In default installation settings, add the "bot" scope
4. The bot requires permissions "Add Reactions", "Attatch Files", "Send Messages", "View Channels", and "View Audit Log" If the default user permissions in your already allow this, this is not required
5. Save changes
6. Copy the discord provided install link, and paste it in your browser
7. Add the bot to your server of choice
8. Set the Install link to None and save changes
9. In the Bot tab, copy the bot's token and paste it into TOKEN.txt (You will need to create this file.)
10. Run main.py
## Development
Sonny is built around 2 core philosiphies that contributors should follow as well
* **Generality:** Features should be able to suit any community, while Sonny is built for AstroGreg, its suitable for any community.
* **Extensibility:** As an addon to Generality, features should not be limited to just one function. Ex: instead of starboards, make arbitrary emoji boards

If your code doesnt fit these two requirements, perhaps look at creating an [extension](https://github.com/driftbluestone/sonny-ext-frame) instead! Extensions were created to implement features that dont have to fit every community, take full advantage of them!