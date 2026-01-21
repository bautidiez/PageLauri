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

        # 1. Descubrir tablas en PG
        pg_cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
        pg_tables = [r[0] for r in pg_cur.fetchall()]
        print(f"Tablas encontradas en PG: {pg_tables}")

        # Orden de migración por dependencias
        ordered_tables = [
            'colores', 'talles', 'categorias', 'productos', 
            'stock_talle', 'stock_talles', 'admins', 
            'clientes', 'pedidos', 'detalles_pedido', 
            'promociones_producto', 'promocion_productos_link', 'promocion_categorias_link'
        ]

        # 2. Limpieza (solo las que existen)
        print("\n--- Paso 1: Limpieza ---")
        for table in reversed(ordered_tables):
            if table in pg_tables:
                try:
                    # TRUNCATE CASCADE es potente, lo usamos con cuidado
                    pg_cur.execute(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE;")
                    print(f"  ✓ {table} limpia")
                    pg_conn.commit()
                except Exception as e:
                    pg_conn.rollback()
                    print(f"  ⚠️ Error limpiando {table}: {e}")

        # 3. Migración
        print("\n--- Paso 2: Migración ---")
        for table in ordered_tables:
            if table not in pg_tables: continue
            
            # Verificar si existe en SQLite
            sql_cur.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
            if not sql_cur.fetchone():
                print(f"  ⚠️ Tabla {table} no encontrada en SQLite, saltando.")
                continue

            # Obtener esquema de PG
            pg_cur.execute(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = '{table}'")
            cols_info = {r[0]: r[1] for r in pg_cur.fetchall()}

            # Leer datos
            sql_cur.execute(f"SELECT * FROM {table} " + ("ORDER BY categoria_padre_id ASC NULLS FIRST" if table == 'categorias' else ""))
            rows = sql_cur.fetchall()
            print(f"  Subiendo {table} ({len(rows)} filas)...")

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
                        elif 'numeric' in dtype or 'double' in dtype or 'real' in dtype:
                            placeholders.append("%s::numeric")
                        elif dtype == 'boolean':
                            placeholders.append("%s::boolean")
                        else:
                            placeholders.append("%s")

                sql = f"INSERT INTO {table} ({','.join(cols_to_insert)}) VALUES ({','.join(placeholders)})"
                try:
                    pg_cur.execute(sql, vals)
                except Exception as e:
                    print(f"  ❌ Error en {table} (ID {row_dict.get('id')}): {e}")
                    pg_conn.rollback()
                    raise e
            
            pg_conn.commit()
            print(f"    ✓ OK")

        # 4. Sincronizar secuencias
        print("\n--- Paso 3: Sincronizar Secuencias ---")
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

        # RESUMEN FINAL
        pg_cur.execute("SELECT COUNT(*) FROM productos")
        final_p = pg_cur.fetchone()[0]
        print(f"\n✅ MIGRACIÓN EXITOSA. Total productos en PG: {final_p}")

    except Exception as e:
        print(f"\n💥 ERROR FATAL: {e}")
        if 'pg_conn' in locals(): pg_conn.rollback()
    finally:
        sql_conn.close()
        pg_conn.close()

if __name__ == "__main__":
    migrate()
