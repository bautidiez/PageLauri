import os
import psycopg2
from urllib.parse import urlparse

def repair_db():
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        print("DATABASE_URL not found")
        return

    print(f"Connecting to database...")
    result = urlparse(db_url)
    username = result.username
    password = result.password
    database = result.path[1:]
    hostname = result.hostname
    port = result.port

    try:
        conn = psycopg2.connect(
            database=database,
            user=username,
            password=password,
            host=hostname,
            port=port
        )
        cur = conn.cursor()
        
        # Intentar agregar la columna si no existe
        print("Checking for 'metodo_verificacion' column in 'clientes'...")
        try:
            cur.execute("ALTER TABLE clientes ADD COLUMN metodo_verificacion VARCHAR(20) DEFAULT 'telefono';")
            conn.commit()
            print("Successfully added 'metodo_verificacion' column.")
        except Exception as e:
            conn.rollback()
            if "already exists" in str(e):
                print("Column 'metodo_verificacion' already exists.")
            else:
                print(f"Error adding column: {e}")

        conn.close()
    except Exception as e:
        print(f"Connection error: {e}")

if __name__ == "__main__":
    repair_db()
