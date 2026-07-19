import psycopg2

__all__ = ["run", "cursor", "connection", "check_connection", "close_connection"]
HOST = "localhost"
NAME = "postgres"      # Your database name
USER = "postgres"      # Your PostgreSQL username
PASS = "asdfjkl"  # Your PostgreSQL password
PORT = "5432"

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

except Exception as error:
    print(f"\nError while connecting to PostgreSQL: {error}")

run = cursor.execute

def check_connection():
    cursor.execute("SELECT version();")
    db_version = cursor.fetchone()
    
    print("\n--- Connection Successful! ---")
    print(f"PostgreSQL version: {db_version[0]}\n")

def close_connection():
    cursor.close()
    connection.close()
    print("Database connection closed.")