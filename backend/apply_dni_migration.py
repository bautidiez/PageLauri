import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()
db_url = os.getenv('DATABASE_URL')

if not db_url:
    print("DATABASE_URL not found")
    exit(1)

try:
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()
    
    with open('c:\\Bau\\PagLauri\\backend\\migrations\\add_cliente_dni_to_pedido.sql', 'r') as f:
        sql = f.read()
    
    print(f"Executing SQL: {sql}")
    cur.execute(sql)
    conn.commit()
    print("Migration applied successfully!")
    
    cur.close()
    conn.close()
except Exception as e:
    print(f"Error: {e}")
