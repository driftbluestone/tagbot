import os
from utils import jsonIO
from utils.utils import DIR

if not os.path.exists(f"{DIR}/data/user.json"):
    jsonIO.dump(f"{DIR}/data/user.json",
                {"id": "", "permissions": {}, "roles": []})

if not os.path.exists(f"{DIR}/data/permissions.json"):
    jsonIO.dump(f"{DIR}/data/permissions.json",
                {"edit_permissions": {
                    "display_name": "Edit Permission",
                    "toggleable": False,
                    "default_enabled": False,
                    "role_assignable": True}})

if not os.path.exists(f"{DIR}/data/config.json"):
    jsonIO.dump(f"{DIR}/data/config.json",
                {"command_prefix": "%", "extensions": {}, "bot_admins": []})


