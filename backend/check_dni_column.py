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
    cur.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'pedido' 
        AND column_name = 'cliente_dni'
    """)
    result = cur.fetchone()
    if result:
        print("Column 'cliente_dni' EXISTS")
    else:
        print("Column 'cliente_dni' DOES NOT EXIST")
    
    # Also list all columns for debugging
    cur.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'pedido'
    """)
    columns = cur.fetchall()
    print("\nAll columns in 'pedido' table:")
    for col in columns:
        print(col[0])
        
    cur.close()
    conn.close()
except Exception as e:
    print(f"Error: {e}")
