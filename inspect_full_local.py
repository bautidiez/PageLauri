import sqlite3
import os

db_path = "backend/instance/elvestuario.db"

def inspect_schema(path):
    conn = sqlite3.connect(path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [t[0] for t in cursor.fetchall() if not t[0].startswith('sqlite_')]
    
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table};")
        count = cursor.fetchone()[0]
        print(f"Table: {table} | Rows: {count}")
    
    conn.close()

inspect_schema(db_path)
