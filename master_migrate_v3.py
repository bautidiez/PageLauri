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

        # 1. Asegurar esquema (esto creará las tablas si no existen)
        print("--- Paso 0: Asegurar Esquema ---")
        # No puedo correr db.create_all() fácil acá sin configurar Flask completo,
        # pero puedo intentar crear las tablas básicas o confiar en que el server ya las creó.
        # El server ya corre db.create_all() al iniciar.
        # Si faltan tablas, es mejor intentar capturar el error.

        tables = [
            'admins',
            'categorias',
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

        print("--- Paso 1: Limpieza ---")
        for table in reversed(tables):
            try:
                pg_cur.execute(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE;")
                print(f"✓ {table} limpia")
            except Exception as e:
                pg_conn.rollback()
                print(f"  Nota: No se pudo limpiar {table} (quizás no existe): {e}")
        pg_conn.commit()

        print("\n--- Paso 2: Migración ---")
        for table in tables:
            pg_cur.execute(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = '{table}'")
            pg_cols = {row[0]: row[1] for row in pg_cur.fetchall()}
            if not pg_cols:
                print(f"⚠️ Saltando {table}: No existe en el destino")
                continue

            sql_cur.execute(f"SELECT * FROM {table}")
            rows = sql_cur.fetchall()
            print(f"Migrando {table} ({len(rows)} filas)...")
            
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
                
                # REGLA DE ORO: Si incluimos el ID, usamos OVERRIDING SYSTEM VALUE
                has_id = 'id' in cols
                overriding = "OVERRIDING SYSTEM VALUE" if (has_id and table != 'admins') else ""
                
                sql = f"INSERT INTO {table} ({','.join(cols)}) {overriding} VALUES ({placeholders})"
                
                try:
                    pg_cur.execute(sql, vals)
                except Exception as e:
                    print(f"❌ ERROR en {table} (Row: {row.get('id', 'N/A')}): {e}")
                    pg_conn.rollback()
                    raise e
            
            pg_conn.commit()
            print(f"    ✓ OK")

        # 3. Sincronizar secuencias para que no fallen los próximos INSERTS manuales
        print("\n--- Paso 3: Sincronizar Secuencias ---")
        for table in tables:
            try:
                # Solo para tablas con ID
                pg_cur.execute(f"SELECT pg_get_serial_sequence('{table}', 'id')")
                seq = pg_cur.fetchone()[0]
                if seq:
                    pg_cur.execute(f"SELECT setval('{seq}', (SELECT MAX(id) FROM {table}))")
                    print(f"✓ Secuencia {seq} sincronizada")
            except:
                pg_conn.rollback()

        pg_conn.commit()
        print("\n🏆 MIGRACIÓN COMPLETADA CON ÉXITO")

    except Exception as e:
        print(f"\n❌ FALLO TOTAL: {e}")
    finally:
        sql_conn.close()
        pg_conn.close()

if __name__ == "__main__":
    migrate()
