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

        tables = ['colores', 'talles', 'categorias', 'productos', 'stock_talle', 'stock_talles']

        print("--- PASO 1: Limpieza ---")
        pg_cur.execute("TRUNCATE TABLE stock_talles, stock_talle, productos, categorias, talles, colores RESTART IDENTITY CASCADE;")
        pg_conn.commit()
        print("✓ Tablas limpias")

        # Migrar Productos solo para ver que pasa
        for table in ['colores', 'talles', 'categorias', 'productos']:
            pg_cur.execute(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = '{table}'")
            pg_cols = {row[0]: row[1] for row in pg_cur.fetchall()}
            
            sql_cur.execute(f"SELECT * FROM {table}")
            rows = sql_cur.fetchall()
            print(f"Migrando {table} ({len(rows)} filas)...")

            for row in rows:
                row_dict = dict(row)
                cols = []
                placeholders = []
                vals = []
                for col, dtype in pg_cols.items():
                    if col in row_dict:
                        val = row_dict[col]
                        if val == "" or val == "None": val = None
                        cols.append(col)
                        vals.append(val)
                        if dtype in ('integer', 'bigint'): placeholders.append("%s::integer")
                        else: placeholders.append("%s")
                
                sql = f"INSERT INTO {table} ({','.join(cols)}) VALUES ({','.join(placeholders)})"
                pg_cur.execute(sql, vals)
            
            pg_conn.commit()
            
            # VERIFICACIÓN INMEDIATA
            pg_cur.execute(f"SELECT id FROM {table} ORDER BY id LIMIT 5")
            inserted_ids = [r[0] for r in pg_cur.fetchall()]
            print(f"    ✓ {table} commited. IDs en PG (primeros 5): {inserted_ids}")
            
            if table == 'productos':
                pg_cur.execute("SELECT id FROM productos WHERE id=20")
                if pg_cur.fetchone():
                    print("    ✓ ID 20 EXISTE EN PG")
                else:
                    print("    ❌ ID 20 NO EXISTE EN PG LUEGO DE INSERTARLO")
                    # Vamos a ver que IDs hay cerca del 20
                    pg_cur.execute("SELECT id FROM productos WHERE id BETWEEN 15 AND 25")
                    print(f"    IDs cerca de 20: {[r[0] for r in pg_cur.fetchall()]}")

        # Intentar stock_talles si todo va bien
        print("\nMigrando stock_talles...")
        sql_cur.execute("SELECT * FROM stock_talles")
        rows = sql_cur.fetchall()
        for row in rows:
            row_dict = dict(row)
            # Replicar lógica de inserción...
            pass

    except Exception as e:
        print(f"Error: {e}")
    finally:
        sql_conn.close()
        pg_conn.close()

if __name__ == "__main__":
    migrate()
