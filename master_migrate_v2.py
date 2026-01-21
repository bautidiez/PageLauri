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
            'categorias',
            'colores',
            'talles',
            'productos',
            'stock_talles', # Depende de productos, colores, talles
            'clientes',
            'pedidos',
            'detalles_pedido',
            'promociones_producto',
            'promocion_productos_link',
            'promocion_categorias_link'
        ]

        # 1. Limpiar (con CASCADE)
        print("--- Limpieza ---")
        for table in reversed(tables):
            try:
                pg_cur.execute(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE;")
                print(f"✓ {table} limpia")
            except:
                pg_conn.rollback()
                pg_cur.execute(f"DELETE FROM {table};")
        pg_conn.commit()

        # 2. Migrar
        for table in tables:
            pg_cur.execute(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = '{table}'")
            pg_cols = {row[0]: row[1] for row in pg_cur.fetchall()}
            if not pg_cols: continue

            sql_cur.execute(f"SELECT * FROM {table}")
            rows = sql_cur.fetchall()
            print(f"Migrando {table} ({len(rows)} filas)...")
            
            for row in rows:
                valid_data = {}
                for col, dtype in pg_cols.items():
                    if col in row.keys():
                        val = row[col]
                        # Limpieza
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
                
                # Usar OVERRIDING SYSTEM VALUE si tiene ID serial/identity para asegurar que se use el ID original
                sql = f"INSERT INTO {table} ({','.join(cols)}) VALUES ({placeholders})"
                
                try:
                    pg_cur.execute(sql, vals)
                except Exception as e:
                    print(f"❌ ERROR en {table} (Row: {row.get('id', 'N/A')}): {e}")
                    # Reintentar con commit parcial o loggear
                    pg_conn.rollback()
                    raise e
            
            pg_conn.commit()
            
            # Verificar
            pg_cur.execute(f"SELECT COUNT(*) FROM {table}")
            count = pg_cur.fetchone()[0]
            print(f"    ✓ OK! Destino tiene {count} filas.")

        print("\n🏆 MIGRACIÓN COMPLETADA CON ÉXITO")

    except Exception as e:
        print(f"\n❌ FALLO TOTAL: {e}")
        if 'pg_conn' in locals(): pg_conn.rollback()
    finally:
        sql_conn.close()
        pg_conn.close()

if __name__ == "__main__":
    migrate()
