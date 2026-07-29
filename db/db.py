import psycopg
from psycopg import sql
from pathlib import Path
from typing import Any
from utils import jsonIO
from utils.logger import Logger

DIR = Path(__file__).parent.parent.resolve()

__all__ = ["SCHEMA", "run", "single", "multiple", "insert", "delete", "get"]

logger = Logger()
data = jsonIO.load(f"{DIR}/bot_info.json")["DB"]
SCHEMA = data["SCHEMA"]

def check_connection():
    cursor.execute("SELECT version();")
    db_version = cursor.fetchone()
    
    logger._logger.info("Connection Successful")
    logger._logger.info(f"PostgreSQL version: {db_version[0]}")

def close_connection():
    cursor.close()
    connection.close()
    logger._logger.info("Database connection closed.")

def run(*args):
    cursor.execute(*args)
    connection.commit()

def single(*args):
    cursor.execute(*args)
    result = cursor.fetchone()
    if isinstance(result, tuple) and len(result) == 1:
        return result[0]
    return result

def multiple(*args):
    cursor.execute(*args)
    return cursor.fetchall()

SCHEMA = sql.Identifier(SCHEMA)

def insert(table: str, key: tuple[str, ...], field: tuple[str, ...], value: tuple[Any, ...]):
    """Actually an upsert function."""
    if not isinstance(key, tuple):
        raise ValueError("Argument `key` must be a tuple.")
    if not isinstance(field, tuple):
        raise ValueError("Argument `field` must be a tuple.")
    if not isinstance(value, tuple):
        raise ValueError("Argument `value` must be a tuple.")
    if len(key) + len(field) != len(value):
        raise ValueError("len(key) + len(field) must equal len(value).")
    if not key:
        raise ValueError("Arguments `key`, `field`, and `value` cannot be empty.")
    
    query = "INSERT INTO {schema}.{table} ({fields}) VALUES ({values}) ON CONFLICT ({keys}) DO"
    if field:
        query += " UPDATE SET {assignments}"
    else:
        query += " NOTHING"

    query = sql.SQL(query).format(
        schema = SCHEMA,
        table = sql.Identifier(table),
        fields = sql.SQL(", ").join(sql.Identifier(f) for f in (key + field)),
        values = sql.SQL(", ").join(sql.Placeholder() for _ in value),
        keys = sql.SQL(", ").join(sql.Identifier(k) for k in key),
        assignments = sql.SQL(", ").join(sql.SQL("{f} = EXCLUDED.{f}").format(
            f=sql.Identifier(f)) for f in field if f not in key
        )
    )
    run(query, value)

def delete(table: str, key: tuple[str, ...], value: tuple[Any, ...]):
    if not isinstance(key, tuple):
        raise ValueError("Argument `key` must be a tuple")
    if not isinstance(value, tuple):
        raise ValueError("Argument `value` must be a tuple")
    if len(key) != len(value):
        raise ValueError("Arguments `key` and `value` must be equal in length")
    if not key:
        raise ValueError("Arguments `key` and `value` cannot be empty")
    
    query = sql.SQL("DELETE FROM {schema}.{table} WHERE {key}").format(
        schema = SCHEMA,
        table = sql.Identifier(table),
        key = sql.SQL(" AND ").join(sql.SQL("{k} = %s").format(
            k = sql.Identifier(k)) for k in key
        )
    )
    run(query, value)

def get(table: str, value: tuple[Any], key: tuple[str], column: tuple[str]):
    if not isinstance(key, tuple):
        raise ValueError("Argument `key` must be a tuple")
    if not isinstance(value, tuple):
        raise ValueError("Argument `value` must be a tuple")
    if len(key) != len(value):
        raise ValueError("Arguments `key` and `value` must be equal in length")
    if not key:
        raise ValueError("Arguments `key` and `value` cannot be empty")
    
    query = sql.SQL("SELECT {column} FROM {schema}.{table} WHERE {key}").format(
        schema = SCHEMA,
        table = sql.Identifier(table),
        column = sql.SQL(", ").join(sql.Identifier(c) for c in column), # CANNOT PUT "*" IN HERE
        key = sql.SQL(" AND ").join(sql.SQL("{k} = %s").format(
            k = sql.Identifier(k)) for k in key
        )
    )
    
    return single(query, value)

def _init():
    """
    Internal function. Creates the schema and tables.
    """
    connection.execute(f"CREATE SCHEMA IF NOT EXISTS {SCHEMA.as_string()};")
    
    # permissions table
    connection.execute(f"""
        CREATE TABLE IF NOT EXISTS {SCHEMA.as_string()}.permissions (
            server_id BIGINT NOT NULL,
            permission TEXT NOT NULL,
            id BIGINT NOT NULL,
            value BOOLEAN,
            PRIMARY KEY (server_id, id, permission)
        );
    """)

    # user data table
    connection.execute(f"""
        CREATE TABLE IF NOT EXISTS {SCHEMA.as_string()}.user (
            server_id BIGINT,
            user_id BIGINT,
            data JSONB,
            PRIMARY KEY (server_id, user_id)
        );
        """)

    # server data table
    connection.execute(f"""
        CREATE TABLE IF NOT EXISTS {SCHEMA.as_string()}.server (
            server_id BIGINT PRIMARY KEY,
            command_prefix TEXT
        );
    """)

    # extension table
    connection.execute(f"""
        CREATE TABLE IF NOT EXISTS {SCHEMA.as_string()}.extensions (
            server_id BIGINT,
            extension TEXT,
            PRIMARY KEY (server_id, extension)
        );
    """)

    # permission metadata table
    connection.execute(f"""
        CREATE TABLE IF NOT EXISTS {SCHEMA.as_string()}.perm (
            name TEXT PRIMARY KEY,
            display_name TEXT,
            toggleable BOOLEAN,
            default_enabled BOOLEAN,
            source TEXT
        );    
    """)

    # message history table
    connection.execute(f"""
        CREATE TABLE IF NOT EXISTS {SCHEMA.as_string()}.history (
            message BIGINT PRIMARY KEY,
            reply BIGINT
        );
    """)
    
    logger._logger.info("Defined Schema and Tables")

logger._logger.info("Connecting to the PostgreSQL database...")
connection = psycopg.connect(
    host=data["HOST"],
    dbname=data["NAME"],
    user=data["USER"],
    password=data["PASS"],
    port=data["PORT"]
)
cursor = connection.cursor()
check_connection()
_init()
insert("perm", ("name",), ("display_name", "toggleable", "default_enabled", "source"), ("#:edit_permissions", "Edit Permissions", False, False, "#"))
insert("perm", ("name",), ("display_name", "toggleable", "default_enabled", "source"), ("#:manage_extensions", "Manage Extensions", False, False, "#"))