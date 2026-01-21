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
            'admins',
            'categorias', # Volvemos a procesar para seguridad
            'colores',
            'talles',
            'productos',
            'stock_talles',
            'clientes',
            'pedidos',
            'detalles_pedido',
            'promociones_producto',
            'promocion_productos_link',
            'promocion_categorias_link'
        ]

        print("--- PASO 1: Limpieza de Base de Datos ---")
        for table in reversed(tables):
            try:
                pg_cur.execute(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE;")
                print(f"✓ {table} limpiada")
            except:
                pg_conn.rollback()
                try:
                    pg_cur.execute(f"DELETE FROM {table};")
                    print(f"✓ {table} borrada (manual)")
                except:
                    pg_conn.rollback()
                    print(f"  Nota: {table} no existe o no se pudo borrar")
        pg_conn.commit()

        print("\n--- PASO 2: Migración de Datos ---")
        for table in tables:
            # 1. Obtener esquema de PG
            pg_cur.execute(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = '{table}'")
            pg_cols = {row[0]: row[1] for row in pg_cur.fetchall()}
            if not pg_cols:
                print(f"⚠️ Saltando {table}: No existe en el destino")
                continue

            # 2. Leer de SQLite
            # Categorías requieren orden especial
            order_by = ""
            if table == 'categorias': order_by = "ORDER BY categoria_padre_id ASC NULLS FIRST, id ASC"
            
            sql_cur.execute(f"SELECT * FROM {table} {order_by}")
            rows = sql_cur.fetchall()
            if not rows:
                print(f"  {table}: 0 filas")
                continue

            print(f"  Migrando {table} ({len(rows)} filas)...")
            
            for row in rows:
                valid_data = {}
                for col, dtype in pg_cols.items():
                    if col in row.keys():
                        val = row[col]
                        if val == "" or val == "None" or val is None:
                            valid_data[col] = None
                        elif dtype in ('integer', 'bigint'):
                            try: valid_data[col] = int(val)
                            except: valid_data[col] = None
                        elif dtype == 'boolean':
                            valid_data[col] = bool(val) if val is not None else None
                        else:
                            valid_data[col] = str(val)
                    else:
                        valid_data[col] = None

                cols = list(valid_data.keys())
                vals = [valid_data[c] for c in cols]
                placeholders = ",".join(["%s"] * len(cols))
                sql = f"INSERT INTO {table} ({','.join(cols)}) VALUES ({placeholders})"
                pg_cur.execute(sql, vals)
            
            pg_conn.commit()
            print(f"    ✓ OK")

        print("\n🏆 MIGRACIÓN COMPLETADA CON ÉXITO")
        
        # Conteo final
        pg_cur.execute("SELECT COUNT(*) FROM productos")
        total_p = pg_cur.fetchone()[0]
        print(f"Resumen Final: {total_p} productos migrados.")

    except Exception as e:
        print(f"\n❌ ERROR CRÍTICO: {e}")
        if 'pg_conn' in locals(): pg_conn.rollback()
    finally:
        if 'sql_conn' in locals(): sql_conn.close()
        if 'pg_conn' in locals(): pg_conn.close()

if __name__ == "__main__":
    migrate()
