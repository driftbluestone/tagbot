# Sonny
This is the bot used in the [AstroGreg discord](https://discord.gg/dUaZeV6Drp)

## Usage Guide
### Permissions
* Accessed by using the /permissions command
* Requires administrator permission or the edit permissions bot permission
* The optional user input field allows managing the permissions of other users
#### Bot admins
* Bot admins bypass all permission checks
* They are also the only people who can manage bot extensions, not even server administrators can
* Bot admins can only be created by adding the user id to the bot admins list in config.json
* NEVER give this permission to people you do not trust, this permission gives them access to download and execute arbitrary github repositories
### Extensions
* A system for adding to bot functionality without interfering with the core bot logic
* Extensions can *only* be managed by bot admins
* Using /extension-add requires that you paste a github link in, which will then install the extension from that repo

## Setup Guide
### Requirements
* Python 3.14+
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
10. Run run.py
