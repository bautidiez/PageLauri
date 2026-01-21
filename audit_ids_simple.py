import sqlite3
import psycopg2

SQLITE_DB = "backend/instance/elvestuario.db"
POSTGRES_URL = "postgresql://elvestuario_user:IbkOl9uuqKVHSae7WWJ9nPox6mXl9YSC@dpg-d5nqgrngi27c73ea03hg-a.oregon-postgres.render.com/elvestuario"

def migrate():
    try:
        sql_conn = sqlite3.connect(SQLITE_DB)
        sql_conn.row_factory = sqlite3.Row
        sql_cur = sql_conn.cursor()
        
        pg_conn = psycopg2.connect(POSTGRES_URL)
        pg_cur = pg_conn.cursor()

        # Simple Clean
        print("Cleaning productos...")
        pg_cur.execute("TRUNCATE TABLE productos RESTART IDENTITY CASCADE;")
        pg_conn.commit()

        # Migrate
        sql_cur.execute("SELECT * FROM productos ORDER BY id")
        rows = sql_cur.fetchall()
        print(f"Migrating {len(rows)} products...")
        
        for row in rows:
            row_dict = dict(row)
            # Solo columnas básicas para prueba
            cols = ['id', 'nombre', 'precio_base', 'activo']
            vals = [row_dict.get(c) for c in cols]
            
            sql = f"INSERT INTO productos ({','.join(cols)}) VALUES (%s, %s, %s, %s)"
            pg_cur.execute(sql, vals)
        
        pg_conn.commit()
        print("Done.")

        pg_cur.execute("SELECT id FROM productos ORDER BY id")
        final_ids = [r[0] for r in pg_cur.fetchall()]
        print(f"IDs in PG: {final_ids}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        sql_conn.close()
        pg_conn.close()

if __name__ == "__main__":
    migrate()
