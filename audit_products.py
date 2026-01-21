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

        # Step 1: Precise Clean
        print("Cleaning...")
        pg_cur.execute("TRUNCATE TABLE stock_talles, stock_talle, productos CASCADE;")
        pg_conn.commit()

        # Step 2: Migrate Products
        sql_cur.execute("SELECT * FROM productos ORDER BY id")
        rows = sql_cur.fetchall()
        print(f"Migrating {len(rows)} products...")
        
        for row in rows:
            row_dict = dict(row)
            # Use only known columns
            cur_cols = ['id', 'nombre', 'precio_base', 'activo', 'categoria_id']
            vals = [row_dict.get(c) for c in cur_cols]
            # Ensure types
            if vals[0]: vals[0] = int(vals[0])
            if vals[2]: vals[2] = float(vals[2])
            
            sql = f"INSERT INTO productos ({','.join(cur_cols)}) VALUES (%s::integer, %s, %s::numeric, %s::boolean, %s::integer)"
            pg_cur.execute(sql, vals)
        
        pg_conn.commit()
        print("Committed products.")

        # Step 3: AUDIT
        pg_cur.execute("SELECT id FROM productos ORDER BY id")
        final_ids = [r[0] for r in pg_cur.fetchall()]
        print(f"Found {len(final_ids)} products in PG.")
        print(f"Max ID: {max(final_ids) if final_ids else 'N/A'}")
        
        if 20 in final_ids:
            print("✓ ID 20 IS PRESENT in PG!")
        else:
            print("❌ ID 20 IS MISSING in PG!")
            # Find closest
            closest = [i for i in final_ids if 15 <= i <= 25]
            print(f"IDs around 20 range: {closest}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        sql_conn.close()
        pg_conn.close()

if __name__ == "__main__":
    migrate()
