from db.db import *
from api import _ext

def table(name: str, columns: list[str]):
    """
    Create a table. Columns should be formatted like `column_name TYPE` e.g. `server_id BIGINT PRIMARY KEY` or `data JSONB`
    """
    if ":" in name:
        name = name.replace(":", "$")
    if "$" not in name:
        name = f"{_ext()}${name}"
    run(f"CREATE TABLE IF NOT EXISTS {name} ({", ".join(columns)});")
