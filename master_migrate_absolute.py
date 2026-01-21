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

        # 1. Discover existing tables
        pg_cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
        pg_tables = [r[0] for r in pg_cur.fetchall()]

        ordered_tables = [
            'colores', 'talles', 'categorias', 'productos', 
            'stock_talle', 'stock_talles', 'admins', 
            'clientes', 'pedidos', 'detalles_pedido', 
            'promociones_producto', 'promocion_productos_link', 'promocion_categorias_link'
        ]

        # 2. Reset everything
        print("--- PASO 1: Reset total ---")
        tables_to_clean = [t for t in ordered_tables if t in pg_tables]
        pg_cur.execute(f"TRUNCATE TABLE {','.join(tables_to_clean)} RESTART IDENTITY CASCADE;")
        pg_conn.commit()
        print("✓ Tablas vaciadas.")

        # 3. Migrate
        print("\n--- PASO 2: Migración con IDs Forzados ---")
        for table in ordered_tables:
            if table not in pg_tables: continue
            
            sql_cur.execute(f"SELECT * FROM {table} " + ("ORDER BY categoria_padre_id ASC NULLS FIRST" if table == 'categorias' else ""))
            rows = sql_cur.fetchall()
            print(f"  {table}: {len(rows)} filas.")

            # Schema info to handle columns correctly
            pg_cur.execute(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = '{table}'")
            pg_cols = {r[0]: r[1] for r in pg_cur.fetchall()}

            for row in rows:
                row_dict = dict(row)
                cols_to_use = []
                casts = []
                values = []
                for col, dtype in pg_cols.items():
                    if col in row_dict:
                        val = row_dict[col]
                        if val == "" or val == "None": val = None
                        
                        cols_to_use.append(col)
                        
                        # FORCE INT FOR ALL IDs
                        if col == 'id' or col.endswith('_id'):
                            try: val = int(val) if val is not None else None
                            except: val = None
                            casts.append("%s::integer")
                        elif dtype in ('integer', 'bigint', 'smallint'):
                            try: val = int(val) if val is not None else None
                            except: val = None
                            casts.append("%s::integer")
                        elif 'numeric' in dtype or 'double' in dtype:
                            try: val = float(val) if val is not None else None
                            except: val = None
                            casts.append("%s::numeric")
                        elif 'bool' in dtype:
                            try: val = bool(val) if val is not None else None
                            except: val = None
                            casts.append("%s::boolean")
                        else:
                            val = str(val) if val is not None else None
                            casts.append("%s")
                        
                        values.append(val)

                if not cols_to_use: continue
                
                sql = f"INSERT INTO {table} ({','.join(cols_to_use)}) VALUES ({','.join(casts)})"
                try:
                    pg_cur.execute(sql, values)
                except Exception as e:
                    print(f"    ❌ Error en {table} (ID {row_dict.get('id')}): {e}")
                    # Mostramos los valores para debug
                    print(f"    Values: {values}")
                    pg_conn.rollback()
                    raise e
            
            pg_conn.commit()
            print(f"    ✓ OK")

        # 4. Sync Sequences
        print("\n--- PASO 3: Sincronización final ---")
        for table in tables_to_clean:
            try:
                pg_cur.execute(f"SELECT pg_get_serial_sequence('{table}', 'id')")
                seq = pg_cur.fetchone()[0]
                if seq:
                    pg_cur.execute(f"SELECT setval('{seq}', (SELECT COALESCE(MAX(id), 1) FROM {table}))")
            except:
                pg_conn.rollback()
        pg_conn.commit()

        print("\n🏆 MIGRACIÓN EXITOSA")

    except Exception as e:
        print(f"\n💥 ERROR FATAL: {e}")
    finally:
        sql_conn.close()
        pg_conn.close()

if __name__ == "__main__":
    migrate()
