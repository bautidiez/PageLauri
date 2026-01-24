import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()
db_url = os.getenv('DATABASE_URL')

output_path = 'c:\\Bau\\PagLauri\\backend\\schema_results_final.txt'

with open(output_path, 'w') as f:
    if not db_url:
        f.write("DATABASE_URL not found\n")
        exit(1)

    try:
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'pedidos' 
            AND column_name = 'cliente_dni'
        """)
        result = cur.fetchone()
        if result:
            f.write("Column 'cliente_dni' EXISTS in 'pedidos'\n")
        else:
            f.write("Column 'cliente_dni' DOES NOT EXIST in 'pedidos'\n")
        
        cur.close()
        conn.close()
    except Exception as e:
        f.write(f"Error: {e}\n")
