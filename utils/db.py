import psycopg2
from utils.utils import data

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
    
    print("\n--- Connection Successful! ---")
    print(f"PostgreSQL version: {db_version[0]}\n")

def close_connection():
    cursor.close()
    connection.close()
    print("Database connection closed.")

try:
    # 2. Establish the database connection
    print("Connecting to the PostgreSQL database...")
    connection = psycopg2.connect(
        host=HOST,
        database=NAME,
        user=USER,
        password=PASS,
        port=PORT
    )
    
    cursor = connection.cursor()
    check_connection()

except Exception as error:
    print(f"\nError while connecting to PostgreSQL: {error}")

def run(*args):
    cursor.execute(*args)
    connection.commit()

def query(*args):
    cursor.execute(*args)
    return cursor.fetchall()

def single(*args):
    cursor.execute(*args)
    return cursor.fetchone()

def insert(table, variables: tuple[str], values: tuple):
    run(f"""INSERT INTO sonny.{table} ({", ".join(variables)}) VALUES ({", ".join(("%s",) * len(values))})
        ON CONFLICT ({variables[0]}) DO UPDATE SET {", ".join(f"{v} = EXCLUDED.{v}" for v in variables if v != variables[0])}
        """, values)

def insert_exclusive(table, variables: tuple[str], values: tuple):
    run(f"INSERT INTO sonny.{table} ({", ".join(variables)}) VALUES ({", ".join(("%s",) * len(values))}", values)

def delete(table, key, value):
    run(f"DELETE FROM sonny.{table} WHERE {key} = %s", (value,))

def get(table, value, column: str | tuple[str] = "*", key: str = "id"):
    return single(f"SELECT {column} FROM sonny.{table} WHERE {key} = %s", (value,))