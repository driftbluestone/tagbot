from typing import Literal
from utils import db
from api import _ext

def table(name: str, custom_serial: bool, columns: dict[str, Literal["SMALLINT", "INT", "BIGINT",
                                                "NUMERIC", "TEXT", "BOOLEAN",
                                                "DOUBLE PRECISION", "SERIAL",
                                                "BIGSERIAL", "TEXT", "JSONB",
                                                "TIMESTAMP", "TIMESTAMPTZ",
                                                "DATE", "TIME", "INTERVAL"]]):
    """
    Create a table
    """
    if ":" in name:
        name = name.replace(":", "$")
    if "$" not in name:
        name = f"{_ext()}${name}"
    if not custom_serial:
        db.run(f"CREATE TABLE IF NOT EXISTS {name} ({', '.join([f'{k} {v}' for k, v in columns.items()])});")
    else:
        pass

def table_info(name: str):
    """
    Get table column names and data types
    """
    return db.query(f"""
                    SELECT column_name, data_type
                    FROM information_schema.columns
                    WHERE table_schema = 'sonny'
                    AND table_name = '{name}'
                    ORDER BY ordinal_position;
                    """)