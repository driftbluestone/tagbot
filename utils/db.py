import psycopg
from utils.logger import Logger
from utils.utils import data

logger = Logger()

__all__ = ["run", "query", "cursor", "connection", "check_connection", "close_connection"]

data = data["DB"]
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

def query(*args):
    connection.execute(*args)
    return cursor.fetchall()

def single(*args):
    connection.execute(*args)
    return cursor.fetchone()

def insert(table: str, variables: tuple[str], values: tuple[any]):
    run(f"""INSERT INTO sonny.{table} ({", ".join(variables)}) VALUES ({", ".join(("%s",) * len(values))})
        ON CONFLICT ({variables[0]}) DO UPDATE SET {", ".join(f"{v} = EXCLUDED.{v}" for v in variables if v != variables[0])}
        """, values)

def insert_exclusive(table: str, variables: tuple[str], values: tuple[any]):
    run(f"INSERT INTO sonny.{table} ({", ".join(variables)}) VALUES ({", ".join(("%s",) * len(values))}", values)

def delete(table: str, key: str, value: any):
    run(f"DELETE FROM sonny.{table} WHERE {key} = %s", (value,))

def get(table: str, value: str, column: str | tuple[str] = "*", key: str = "id") -> tuple[any]:
    if isinstance(column, tuple):
        column = ", ".join(column)
    return single(f"SELECT {column} FROM sonny.{table} WHERE {key} = %s", (value,))