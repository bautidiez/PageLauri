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

        # 1. DESCUBRIR TABLAS
        pg_cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
        pg_tables = [r[0] for r in pg_cur.fetchall()]

        ordered_tables = [
            'colores', 'talles', 'categorias', 'productos', 
            'stock_talle', 'stock_talles', 'admins', 
            'clientes', 'pedidos', 'detalles_pedido', 
            'promociones_producto', 'promocion_productos_link', 'promocion_categorias_link'
        ]

        print("--- PASO 1: Deshabilitar FK y Limpiar ---")
        try:
            # Deshabilitar FKs para esta sesión (truco de réplica)
            pg_cur.execute("SET session_replication_role = 'replica';")
            print("✓ FKs deshabilitadas temporalmente")
        except Exception as e:
            print(f"⚠️ No se pudo deshabilitar FKs: {e}")

        for table in reversed(ordered_tables):
            if table in pg_tables:
                pg_cur.execute(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE;")
        pg_conn.commit()
        print("✓ Tablas limpias")

        print("\n--- PASO 2: Migración Masiva ---")
        for table in ordered_tables:
            if table not in pg_tables: continue
            
            # Esquema PG
            pg_cur.execute(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = '{table}'")
            cols_info = {r[0]: r[1] for r in pg_cur.fetchall()}

            # Datos SQLite
            sql_cur.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
            if not sql_cur.fetchone(): continue

            sql_cur.execute(f"SELECT * FROM {table}")
            rows = sql_cur.fetchall()
            if not rows: continue
            
            print(f"  Migrando {table} ({len(rows)} filas)...")
            
            for row in rows:
                row_dict = dict(row)
                cols_to_insert = []
                placeholders = []
                vals = []
                
                for col, dtype in cols_info.items():
                    if col in row_dict:
                        val = row_dict[col]
                        if val == "" or val == "None": val = None
                        
                        cols_to_insert.append(col)
                        vals.append(val)
                        
                        if dtype in ('integer', 'bigint', 'smallint'):
                            placeholders.append("%s::integer")
                        elif 'numeric' in dtype or 'double' in dtype:
                            placeholders.append("%s::numeric")
                        elif dtype == 'boolean':
                            placeholders.append("%s::boolean")
                        else:
                            placeholders.append("%s")

                sql = f"INSERT INTO {table} ({','.join(cols_to_insert)}) VALUES ({','.join(placeholders)})"
                pg_cur.execute(sql, vals)
            
            # Commit por tabla
            pg_conn.commit()
            print(f"    ✓ OK")

        # 4. Habilitar FKs y sincronizar secuencias
        print("\n--- PASO 3: Restauración ---")
        pg_cur.execute("SET session_replication_role = 'origin';")
        
        for table in pg_tables:
            try:
                pg_cur.execute(f"SELECT pg_get_serial_sequence('{table}', 'id')")
                seq = pg_cur.fetchone()[0]
                if seq:
                    pg_cur.execute(f"SELECT setval('{seq}', (SELECT COALESCE(MAX(id), 1) FROM {table}))")
            except:
                pg_conn.rollback()
        
        pg_conn.commit()
        
        # Validación final
        pg_cur.execute("SELECT COUNT(*) FROM productos")
        count = pg_cur.fetchone()[0]
        print(f"\n✅ MIGRACIÓN FINALIZADA. Productos en PG: {count}")

    except Exception as e:
        print(f"\n💥 ERROR: {e}")
        if 'pg_conn' in locals(): pg_conn.rollback()
    finally:
        sql_conn.close()
        pg_conn.close()

if __name__ == "__main__":
    migrate()
