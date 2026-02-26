# Sonny
This is the bot used in the [AstroGreg discord](https://discord.gg/dUaZeV6Drp)

Features:
* Tags
* Edit & Delete message logging
* Sed functionality
* Message link embedding
## Usage Guide
### Tags
* Use %t to look at tag information
* Code tags are any tag that start with ``` on the same line as %t add
* usage of %t admin or any subcommands requires either administrator permissions, or the tag_admin flag on your user profile to be enabled
* enabling tag_admin on a user profile is done via %t admin promote "user"
### Sed
* Usage: sed/"text to replace"/"text to replace it with"
* Supports regex matching
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
4. The bot requires permissions "Add Reactions", "Attatch Files", "Send Messages", and "View Channels" If the default user permissions in your already allow this, this is not required
5. Save changes
6. Copy the discord provided install link, and paste it in your browser
7. Add the bot to your server of choice
8. Set the Install link to None and save changes
9. In the Bot tab, copy the bot's token and paste it into TOKEN.txt (you will need to create that file)
10. In config.json, set the ID of the channel you would like to use for message edit & delete logging, set to 0 to disable
11. run main.py
### Troubleshooting
* If there are issues with the code tags, try changing the docker function
1. Change line 304 to "docargs = \['sudo', 'docker', 'run',"
2. Change line 310 to 'python', 'python3', f'/data/{tag}.py'\]
