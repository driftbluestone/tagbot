import json
from contextlib import closing
import psycopg2


DB_HOST = "localhost"
DB_NAME = "postgres"      # Your database name
DB_USER = "postgres"      # Your PostgreSQL username
DB_PASS = "asdfjkl"  # Your PostgreSQL password
DB_PORT = "5432"

with closing(psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASS, port=DB_PORT)) as connection:
        
        # 2. This 'with' block manages the transaction (automatic commit if successful)
        with connection:
            
            # 3. This 'with' block automatically closes the cursor when done
            with connection.cursor() as cursor:
                
                cursor.execute("DROP SCHEMA IF EXISTS sonny CASCADE;")
                print("Creating schema and table...")
                
                cursor.execute("CREATE SCHEMA IF NOT EXISTS sonny;")
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS sonny.users (
                        name SERIAL PRIMARY KEY,
                        id BIGINT,
                        perms JSONB,
                        data JSONB
                    );
                """)
                
                print("Schema and Table defined successfully!")

id = 887176924932210748

perms = {
    "sonny_tags:admin": None,
    "sonny_tags:view": None,
    "sonny_tags:create": False,
    "edit_permissions": True
}

data = {
     "sonny_tags:tags": [
          "iq",
          "drift",
          "bgame"
     ]
}

with closing(psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASS, port=DB_PORT)) as connection:
        
    # 2. This 'with' block manages the transaction (automatic commit if successful)
    with connection:
        
        # 3. This 'with' block automatically closes the cursor when done
        with connection.cursor() as cursor:
            
            insert_query = "INSERT INTO sonny.users (id, perms, data) VALUES (%s, %s, %s);"
        
            # Use json.dumps() to convert the Python dict into a JSON string
            cursor.execute(insert_query, (id, json.dumps(perms), json.dumps(data)))
            print("Successfully inserted JSONB entry!")

            select_query = """
                SELECT 
                    id, 
                    perms,
                    data
                FROM sonny.users 
                WHERE id = %s;
            """
            
            cursor.execute(select_query, (id,))
            row = cursor.fetchone()
            
            if row:
                id, perms, data = row
                print("\n--- Data Read from Database ---")
                print(f"id: {id}")
                print(f"perms: {perms}")
                print(f"data: {data}")

def execute_in_db(command: str):
    with closing(psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASS, port=DB_PORT)) as connection:
        
        # 2. This 'with' block manages the transaction (automatic commit if successful)
        with connection:
            
            # 3. This 'with' block automatically closes the cursor when done
            with connection.cursor() as cursor:
                cursor.execute(command)

