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

        print("Cleaning productos...")
        pg_cur.execute("TRUNCATE TABLE productos RESTART IDENTITY CASCADE;")
        pg_conn.commit()

        sql_cur.execute("SELECT id, nombre, precio_base, activo FROM productos ORDER BY id")
        rows = sql_cur.fetchall()
        print(f"Migrating {len(rows)} products...")

        for row in rows:
            # FORCE TYPES
            pid = int(row['id'])
            pname = str(row['nombre'])
            pprice = float(row['precio_base']) if row['precio_base'] else 0.0
            pact = bool(row['activo'])
            
            # Using tuple to be sure
            pg_cur.execute("INSERT INTO productos (id, nombre, precio_base, activo) VALUES (%s, %s, %s, %s)", 
                           (pid, pname, pprice, pact))
            
        pg_conn.commit()
        print("Commit successful.")

        pg_cur.execute("SELECT COUNT(*) FROM productos")
        print(f"Total in PG: {pg_cur.fetchone()[0]}")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        sql_conn.close()
        pg_conn.close()

if __name__ == "__main__":
    test()
