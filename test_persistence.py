import sqlite3
import psycopg2

SQLITE_DB = "backend/instance/elvestuario.db"
POSTGRES_URL = "postgresql://elvestuario_user:IbkOl9uuqKVHSae7WWJ9nPox6mXl9YSC@dpg-d5nqgrngi27c73ea03hg-a.oregon-postgres.render.com/elvestuario"

def test():
    try:
        sql_conn = sqlite3.connect(SQLITE_DB)
        sql_conn.row_factory = sqlite3.Row
        sql_cur = sql_conn.cursor()
        
        pg_conn = psycopg2.connect(POSTGRES_URL)
        pg_cur = pg_conn.cursor()

        print("Cleaning...")
        pg_cur.execute("TRUNCATE TABLE stock_talles, productos CASCADE;")
        pg_conn.commit()

        sql_cur.execute("SELECT id, nombre, categoria_id, precio_base, activo FROM productos")
        rows = sql_cur.fetchall()
        print(f"Migrating {len(rows)} products...")

        for row in rows:
            pg_cur.execute("INSERT INTO productos (id, nombre, categoria_id, precio_base, activo) VALUES (%s, %s, %s, %s, %s)", 
                           (int(row['id']), str(row['nombre']), int(row['categoria_id']), float(row['precio_base']), bool(row['activo'])))
        
        pg_conn.commit()
        print("✓ Committed.")
        
        pg_cur.close()
        pg_conn.close()
        
        # REOPEN
        print("Reopening to verify...")
        pg_conn = psycopg2.connect(POSTGRES_URL)
        pg_cur = pg_conn.cursor()
        pg_cur.execute("SELECT COUNT(*) FROM productos")
        count = pg_cur.fetchone()[0]
        print(f"Count in PG: {count}")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        sql_conn.close()
        if 'pg_conn' in locals(): pg_conn.close()

if __name__ == "__main__":
    test()
