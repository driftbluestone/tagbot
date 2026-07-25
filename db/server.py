from typing import Literal
from db import db

def server(server_id: int, fields: tuple[Literal["perms", "extensions", "default_user_data","command_prefix", "*"], ...]):
    """
    
    """
    if isinstance(fields, str):
        fields = (fields,)
    return db.get("server", (server_id,), ("server_id",), fields)