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

        # Clean
        pg_cur.execute("TRUNCATE TABLE stock_talles CASCADE;")
        pg_cur.execute("TRUNCATE TABLE productos CASCADE;")
        pg_conn.commit()

        # Get PG schema for products
        pg_cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'productos'")
        pg_schema = {r[0]: r[1] for r in pg_cur.fetchall()}

        # Migrate only 20 products
        sql_cur.execute("SELECT * FROM productos ORDER BY id ASC LIMIT 80")
        rows = sql_cur.fetchall()
        print(f"Migrating {len(rows)} products...")

        for row in rows:
            row_dict = dict(row)
            cols = []
            vals = []
            for col in pg_schema.keys():
                if col in row_dict:
                    val = row_dict[col]
                    if val == "" or val == "None" or val is None:
                        val = None
                    cols.append(col)
                    vals.append(val)
            
            placeholders = ",".join(["%s"] * len(cols))
            sql = f"INSERT INTO productos ({','.join(cols)}) VALUES ({placeholders})"
            pg_cur.execute(sql, vals)
            
        pg_conn.commit()
        print("✓ Committed products.")

        # Check in PG
        pg_cur.execute("SELECT id, nombre FROM productos ORDER BY id")
        res = pg_cur.fetchall()
        print(f"Found {len(res)} products in PG.")
        ids = [r[0] for r in res]
        print(f"IDs: {ids}")
        
        if 20 in ids:
            print("✓ ID 20 is present")
        else:
            print("❌ ID 20 is NOT present")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        sql_conn.close()
        pg_conn.close()

if __name__ == "__main__":
    test()
