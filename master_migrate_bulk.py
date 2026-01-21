import sqlite3
import psycopg2
import time

SQLITE_DB = "backend/instance/elvestuario.db"
POSTGRES_URL = "postgresql://elvestuario_user:IbkOl9uuqKVHSae7WWJ9nPox6mXl9YSC@dpg-d5nqgrngi27c73ea03hg-a.oregon-postgres.render.com/elvestuario"

def migrate():
    try:
        sql_conn = sqlite3.connect(SQLITE_DB)
        sql_conn.row_factory = sqlite3.Row
        sql_cur = sql_conn.cursor()
        
        pg_conn = psycopg2.connect(POSTGRES_URL)
        pg_cur = pg_conn.cursor()

        tables = [
            'colores',
            'talles',
            'categorias',
            'productos',
            'stock_talle',
            'stock_talles',
            'admins',
            'clientes',
            'pedidos',
            'detalles_pedido',
            'promociones_producto',
            'promocion_productos_link',
            'promocion_categorias_link'
        ]

        pg_cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
        existing_tables = [r[0] for r in pg_cur.fetchall()]

        print("--- Paso 1: Limpieza ---")
        for table in reversed(tables):
            if table not in existing_tables: continue
            print(f"Limpiando {table}...")
            try:
                pg_cur.execute(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE;")
            except:
                pg_conn.rollback()
                pg_cur.execute(f"DELETE FROM {table};")
        pg_conn.commit()

        print("\n--- Paso 2: Migración con Casting Explícito ---")
        for table in tables:
            if table not in existing_tables: continue
            
            sql_cur.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
            if not sql_cur.fetchone(): continue

            pg_cur.execute(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = '{table}'")
            pg_cols = {row[0]: row[1] for row in pg_cur.fetchall()}

            sql_cur.execute(f"SELECT * FROM {table} " + ("ORDER BY categoria_padre_id ASC NULLS FIRST" if table == 'categorias' else ""))
            rows = sql_cur.fetchall()
            print(f"Migrando {table} ({len(rows)} filas)...")

            for row in rows:
                row_dict = dict(row)
                cols_to_insert = []
                placeholders = []
                vals = []
                
                for col, dtype in pg_cols.items():
                    if col in row_dict:
                        val = row_dict[col]
                        if val == "" or val == "None" or val is None:
                            val = None
                        
                        cols_to_insert.append(col)
                        vals.append(val)
                        
                        # CASTING EXPLÍCITO para tipos numéricos en PG
                        if dtype in ('integer', 'bigint', 'smallint'):
                            placeholders.append("%s::integer")
                        elif 'numeric' in dtype or 'double' in dtype:
                            placeholders.append("%s::numeric")
                        elif dtype == 'boolean':
                            placeholders.append("%s::boolean")
                        else:
                            placeholders.append("%s")

                sql = f"INSERT INTO {table} ({','.join(cols_to_insert)}) VALUES ({','.join(placeholders)})"
                try:
                    pg_cur.execute(sql, vals)
                except Exception as e:
                    print(f"❌ Error en {table} (Row {row_dict.get('id')}): {e}")
                    pg_conn.rollback()
                    raise e
            
            pg_conn.commit()
            print(f"    ✓ OK")

        # 3. Sincronizar secuencias
        print("\n--- Paso 3: Sincronizar Secuencias ---")
        for table in existing_tables:
            try:
                pg_cur.execute(f"SELECT pg_get_serial_sequence('{table}', 'id')")
                seq = pg_cur.fetchone()[0]
                if seq:
                    pg_cur.execute(f"SELECT setval('{seq}', (SELECT COALESCE(MAX(id), 1) FROM {table}))")
                    print(f"✓ {seq} OK")
            except:
                pg_conn.rollback()

        pg_conn.commit()
        print("\n🏆 MIGRACIÓN COMPLETADA CON ÉXITO")

    except Exception as e:
        print(f"\n💥 ERROR: {e}")
    finally:
        sql_conn.close()
        pg_conn.close()

if __name__ == "__main__":
    migrate()
