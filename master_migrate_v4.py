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

        # Tablas en orden estricto de dependencias
        tables = [
            'colores',
            'talles',
            'categorias',
            'productos',
            'stock_talles',
            'admins',
            'clientes',
            'pedidos',
            'detalles_pedido',
            'promociones_producto',
            'promocion_productos_link',
            'promocion_categorias_link'
        ]

        print("--- PASO 1: Limpieza Total ---")
        for table in reversed(tables):
            try:
                pg_cur.execute(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE;")
                print(f"✓ {table} limpia")
            except Exception as e:
                pg_conn.rollback()
                print(f"  (Omitiendo limpieza de {table})")
        pg_conn.commit()

        print("\n--- PASO 2: Migración ---")
        for table in tables:
            # Detectar columnas en PG
            pg_cur.execute(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = '{table}'")
            pg_schema = {r[0]: r[1] for r in pg_cur.fetchall()}
            if not pg_schema: continue

            # Leer SQLite
            sql_cur.execute(f"SELECT * FROM {table} " + ("ORDER BY categoria_padre_id ASC NULLS FIRST" if table == 'categorias' else ""))
            rows = sql_cur.fetchall()
            print(f"Tabla {table}: Procesando {len(rows)} filas...")

            success_count = 0
            for row in rows:
                row_dict = dict(row)
                valid_data = {}
                for col, dtype in pg_schema.items():
                    val = row_dict.get(col)
                    if val == "" or val == "None" or val is None:
                        valid_data[col] = None
                    elif dtype in ('integer', 'bigint'):
                        try: valid_data[col] = int(val)
                        except: valid_data[col] = None
                    elif dtype == 'boolean':
                        valid_data[col] = bool(val) if val is not None else None
                    else:
                        valid_data[col] = str(val)

                cols = list(valid_data.keys())
                vals = [valid_data[c] for c in cols]
                placeholders = ",".join(["%s"] * len(cols))
                
                # Inserción normal sin OVERRIDING
                sql = f"INSERT INTO {table} ({','.join(cols)}) VALUES ({placeholders})"
                
                try:
                    pg_cur.execute(sql, vals)
                    success_count += 1
                except Exception as e:
                    print(f"  ❌ Error en {table} (ID {row_dict.get('id')}): {e}")
                    # Para tablas críticas, queremos saber el error exacto
                    # pero intentaremos seguir si es posible, o abortar si es FK
                    pg_conn.rollback()
                    # Si es un error de integridad, mejor abortar para corregir el script
                    raise e
            
            pg_conn.commit()
            print(f"    ✓ {success_count} filas migradas con éxito.")

        print("\n🏆 MIGRACIÓN COMPLETADA CON ÉXITO")

    except Exception as e:
        print(f"\n💥 ERROR FATAL: {e}")
    finally:
        sql_conn.close()
        pg_conn.close()

if __name__ == "__main__":
    migrate()
