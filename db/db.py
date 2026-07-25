import psycopg
from psycopg import sql
from typing import Any
from utils.logger import Logger
from utils.utils import data

logger = Logger()
data = data["DB"]
SCHEMA = sql.Identifier(data["SCHEMA"])
HOST = data["HOST"]
NAME = data["NAME"]
USER = data["USER"]
PASS = data["PASS"]
PORT = data["PORT"]

def check_connection():
    cursor.execute("SELECT version();")
    db_version = cursor.fetchone()
    
    logger._logger.info("Connection Successful")
    logger._logger.info(f"PostgreSQL version: {db_version[0]}")

def close_connection():
    cursor.close()
    connection.close()
    logger._logger.info("Database connection closed.")

try:
    logger._logger.info("Connecting to the PostgreSQL database...")
    connection = psycopg.connect(
        host=HOST,
        database=NAME,
        user=USER,
        password=PASS,
        port=PORT
    )
    
    cursor = connection.cursor()
    check_connection()

except Exception as error:
    logger._logger.error(f"\nError while connecting to PostgreSQL: {error}")

def run(*args):
    connection.execute(*args)
    connection.commit()

def single(*args):
    connection.execute(*args)
    return cursor.fetchone()

def insert(table: str, key: tuple[str, ...], field: tuple[str, ...], value: tuple[Any, ...]):
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
    
    query = sql.SQL("INSERT INTO {schema}.{table} ({fields}) VALUES ({values}) ON CONFLICT ({keys}) DO UPDATE SET {assignments}").format(
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

def get(table: str, value: tuple[any], key: tuple[str] = ("id",), column: tuple[str] = ("*",)):
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
        column = sql.SQL(", ").join(sql.Identifier(c) for c in column),
        key = sql.SQL(" AND ").join(sql.SQL("{k} = %s").format(
            k = sql.Identifier(k)) for k in key
        )
    )
    return single(query, value)