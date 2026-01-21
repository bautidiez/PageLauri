import sqlite3
import os

db_path = "backend/instance/elvestuario.db"
backup_path = "backend/instance/elvestuario_backup.db"

def check_db(path):
    if not os.path.exists(path):
        print(f"File not found: {path}")
        return
    
    print(f"--- Checking {path} ---")
    try:
        conn = sqlite3.connect(path)
        cursor = conn.cursor()
        
        # Check tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"Tables: {[t[0] for t in tables]}")
        
        if ('productos',) in tables:
            cursor.execute("SELECT COUNT(*) FROM productos;")
            p_count = cursor.fetchone()[0]
            print(f"Products: {p_count}")
        
        if ('categorias',) in tables:
            cursor.execute("SELECT COUNT(*) FROM categorias;")
            c_count = cursor.fetchone()[0]
            print(f"Categories: {c_count}")
            
        conn.close()
    except Exception as e:
        print(f"Error checking {path}: {e}")

check_db(db_path)
print()
check_db(backup_path)
