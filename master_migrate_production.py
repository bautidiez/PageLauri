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

        # 1. Discover tables in PG
        pg_cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
        pg_tables = [r[0] for r in pg_cur.fetchall()]
        print(f"PG Tables: {pg_tables}")

        ordered_tables = [
            'colores', 'talles', 'categorias', 'productos', 
            'stock_talle', 'stock_talles', 'admins', 
            'clientes', 'pedidos', 'detalles_pedido', 
            'promociones_producto'
        ]

        # 2. Dynamic Clean
        print("\n--- PASO 1: Limpieza ---")
        for table in reversed(ordered_tables):
            if table in pg_tables:
                try:
                    pg_cur.execute(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE")
                    print(f"  ✓ {table} limpia")
                    pg_conn.commit()
                except:
                    pg_conn.rollback()

        # 3. Migrate
        print("\n--- PASO 2: Migración ---")
        for table in ordered_tables:
            if table not in pg_tables: continue
            
            # Check SQLite
            sql_cur.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
            if not sql_cur.fetchone(): continue

            pg_cur.execute(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = '{table}'")
            cols_info = {r[0]: r[1] for r in pg_cur.fetchall()}

            sql_cur.execute(f"SELECT * FROM {table} " + ("ORDER BY categoria_padre_id ASC NULLS FIRST" if table == 'categorias' else ""))
            rows = sql_cur.fetchall()
            print(f"  {table}: {len(rows)} filas...")

            for row in rows:
                row_dict = dict(row)
                cols = []
                casts = []
                vals = []
                for col, dtype in cols_info.items():
                    if col in row_dict:
                        val = row_dict[col]
                        if val == "" or val == "None": val = None
                        cols.append(col)
                        vals.append(val)
                        if dtype in ('integer', 'bigint', 'smallint'): casts.append("%s::integer")
                        elif 'numeric' in dtype or 'double' in dtype: casts.append("%s::numeric")
                        elif 'bool' in dtype: casts.append("%s::boolean")
                        else: casts.append("%s")

                sql = f"INSERT INTO {table} ({','.join(cols)}) VALUES ({','.join(casts)})"
                try:
                    pg_cur.execute(sql, vals)
                except Exception as e:
                    print(f"    ❌ Error en {table} (ID {row_dict.get('id')}): {e}")
                    pg_conn.rollback()
                    raise e
            
            pg_conn.commit()
            print(f"    ✓ OK")

        # 4. Sync Sequences
        print("\n--- PASO 3: Secuencias ---")
        for table in pg_tables:
            try:
                pg_cur.execute(f"SELECT pg_get_serial_sequence('{table}', 'id')")
                seq = pg_cur.fetchone()[0]
                if seq:
                    pg_cur.execute(f"SELECT setval('{seq}', (SELECT COALESCE(MAX(id), 1) FROM {table}))")
                    print(f"  ✓ {seq} OK")
            except:
                pg_conn.rollback()
        pg_conn.commit()

        print("\n🏆 MIGRACIÓN FINALIZADA")

    except Exception as e:
        print(f"\n💥 ERROR FATAL: {e}")
    finally:
        sql_conn.close()
        pg_conn.close()

if __name__ == "__main__":
    migrate()
