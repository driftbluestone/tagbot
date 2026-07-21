import psycopg
from psycopg import sql
from utils.logger import Logger
from utils.utils import data

logger = Logger()

__all__ = ["run", "query", "cursor", "connection", "check_connection", "close_connection"]

data = data["DB"]
SCHEMA = data["SCHEMA"]
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

# def query(*args):
#     connection.execute(*args)
#     return cursor.fetchall()

def single(*args):
    connection.execute(*args)
    return cursor.fetchone()

def insert(table: str, variables: tuple[str], values: tuple[any]):
    run(f"""INSERT INTO {SCHEMA}.{table} ({", ".join(variables)}) VALUES ({", ".join(("%s",) * len(values))})
        ON CONFLICT ({variables[0]}) DO UPDATE SET {", ".join(f"{v} = EXCLUDED.{v}" for v in variables if v != variables[0])}
        """, values)

def insert(table: str, fields: tuple[str], values: tuple[any] | any):
    query = sql.SQL("INSERT INTO {schema}.{table} ({fields}) VALUES ({values})").format(
        schema = SCHEMA,
        table = table,
        fields = sql.SQL(", ").join(sql.Identifier(f) for f in fields),
        values = sql.SQL(", ").join(sql.Placeholder() for _ in values)
    )
    run(query)

def insert_exclusive(table: str, variables: tuple[str], values: tuple[any]):
    run(f"INSERT INTO {SCHEMA}.{table} ({", ".join(variables)}) VALUES ({", ".join(("%s",) * len(values))}", values)

def delete(table: str, key: str, value: any):
    run(f"DELETE FROM {SCHEMA}.{table} WHERE {key} = %s", (value,))

def get(table: str, value: str | tuple[str], column: str | tuple[str] = "*", key: str | tuple[str] = "id") -> tuple[any]:
    query = sql.SQL("SELECT {column} FROM {schema}.{table} WHERE {key}").format(
        column = sql.SQL(", ").join(sql.Identifier(c) for c in column) if isinstance(column, tuple) else sql.Identifier(column),
        schema = SCHEMA,
        table = table,
        key = sql.SQL(" AND ").join(sql.SQL("{k} = %s").format(k=sql.Identifier(k)) for k in key) if isinstance(key, tuple) else sql.SQL("{key} = %s").format(key=sql.Identifier(key))
    )
    run(query, (value,) if not isinstance(value, tuple) else value)