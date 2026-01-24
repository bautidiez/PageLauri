import os
import sqlite3

db_path = os.path.join('c:\\Bau\\PagLauri\\backend', 'instance', 'database.db')
if not os.path.exists(db_path):
    print(f"DB not found at {db_path}")
else:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(pedido)")
    columns = cursor.fetchall()
    print("Columns in 'pedido' table:")
    for col in columns:
        print(col[1])
    conn.close()
