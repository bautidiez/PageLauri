
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def diagnose():
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        print("DATABASE_URL not found")
        return

    try:
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        
        # Check sequences
        cur.execute("""
            SELECT relname 
            FROM pg_class 
            WHERE relkind = 'S';
        """)
        sequences = cur.fetchall()
        print("Found sequences:", [s[0] for s in sequences])
        
        # Check max ID in categorias
        cur.execute("SELECT MAX(id) FROM categorias")
        max_id = cur.fetchone()[0]
        print(f"Max ID in categorias: {max_id}")
        
        # Check current value of sequence
        seq_name = 'categorias_id_seq'
        if any(seq_name == s[0] for s in sequences):
            cur.execute(f"SELECT last_value, is_called FROM {seq_name}")
            val = cur.fetchone()
            print(f"Sequence {seq_name} status: last_value={val[0]}, is_called={val[1]}")
        else:
            print(f"Sequence {seq_name} not found in pg_class")
            
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error diagnostics: {e}")

if __name__ == "__main__":
    diagnose()
