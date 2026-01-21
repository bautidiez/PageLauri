import sqlite3
import psycopg2

SQLITE_DB = "backend/instance/elvestuario.db"
POSTGRES_URL = "postgresql://elvestuario_user:IbkOl9uuqKVHSae7WWJ9nPox6mXl9YSC@dpg-d5nqgrngi27c73ea03hg-a.oregon-postgres.render.com/elvestuario"

def test_p():
    sql_conn = sqlite3.connect(SQLITE_DB)
    sql_conn.row_factory = sqlite3.Row
    sql_cur = sql_conn.cursor()
    
    pg_conn = psycopg2.connect(POSTGRES_URL)
    pg_cur = pg_conn.cursor()

    print("Cleaning productos...")
    pg_cur.execute("TRUNCATE TABLE stock_talles, productos CASCADE;")
    pg_conn.commit()

    sql_cur.execute("SELECT * FROM productos")
    rows = sql_cur.fetchall()
    print(f"Migrating {len(rows)} products...")

    for row in rows:
        d = dict(row)
        # Using basic columns to avoid missing ones
        cols = ['id', 'nombre', 'precio_base', 'categoria_id', 'activo']
        vals = [int(d['id']), str(d['nombre']), float(d['precio_base']), int(d['categoria_id']), bool(d['activo'])]
        
        pg_cur.execute("INSERT INTO productos (id, nombre, precio_base, categoria_id, activo) VALUES (%s, %s, %s, %s, %s)", vals)
    
    print("Committing...")
    pg_conn.commit()
    print("Commit done.")

    pg_cur.execute("SELECT COUNT(*), MIN(id), MAX(id) FROM productos")
    res = pg_cur.fetchone()
    print(f"Stats in PG: Count={res[0]}, Min={res[1]}, Max={res[2]}")
    
    pg_cur.execute("SELECT id FROM productos WHERE id=20")
    if pg_cur.fetchone():
        print("✓ ID 20 FOUND")
    else:
        print("❌ ID 20 NOT FOUND")

    pg_cur.close()
    pg_conn.close()
    sql_conn.close()

test_p()
