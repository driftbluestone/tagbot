from db import db

def get(permission: str) -> dict:
    perm = db.get("perm", (permission,), ("name",), ("display_name", "toggleable", "default_enabled"))
    return {
        "name": permission,
        "display_name": perm[0],
        "toggleable": perm[1],
        "default_enabled": perm[2]
    }

def set(server_id: int, id: int, permission: str, value):
    if value is None:
        return
    db.insert("permissions", ("server_id", "id", "permission"), ("value",), (server_id, id, permission, value))