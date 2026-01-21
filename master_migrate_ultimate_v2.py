import sqlite3
import psycopg2
from psycopg2.extras import execute_values

SQLITE_DB = "backend/instance/elvestuario.db"
POSTGRES_URL = "postgresql://elvestuario_user:IbkOl9uuqKVHSae7WWJ9nPox6mXl9YSC@dpg-d5nqgrngi27c73ea03hg-a.oregon-postgres.render.com/elvestuario"

def migrate():
    try:
        sql_conn = sqlite3.connect(SQLITE_DB)
        sql_conn.row_factory = sqlite3.Row
        sql_cur = sql_conn.cursor()
        
        pg_conn = psycopg2.connect(POSTGRES_URL)
        pg_cur = pg_conn.cursor()

        # Tablas que existen en PG segun mis anteriores descubrimientos
        pg_tables = [
            'colores', 'talles', 'categorias', 'productos', 
            'stock_talle', 'stock_talles', 'admins', 
            'clientes', 'pedidos', 'detalles_pedido', 
            'promociones_producto'
        ]

        print("--- PASO 1: Limpieza ---")
        pg_cur.execute("TRUNCATE TABLE stock_talles, stock_talle, detalles_pedido, pedidos, productos, categorias, talles, colores, promociones_producto, clientes, admins RESTART IDENTITY CASCADE")
        pg_conn.commit()
        print("✓ Limpieza OK")

        # Tablas en orden
        migration_order = [
            'colores', 'talles', 'categorias', 'productos', 
            'stock_talles', 'admins', 'clientes', 'pedidos', 'detalles_pedido'
        ]

        for table in migration_order:
            # Esquema PG
            pg_cur.execute(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = '{table}'")
            pg_cols = {r[0]: r[1] for r in pg_cur.fetchall()}
            if not pg_cols: continue

            # Data SQLite
            sql_cur.execute(f"SELECT * FROM {table} " + ("ORDER BY categoria_padre_id ASC NULLS FIRST" if table == 'categorias' else ""))
            rows = sql_cur.fetchall()
            print(f"Migrando {table} ({len(rows)} filas)...")

            if not rows: continue

            for row in rows:
                row_dict = dict(row)
                cols_to_use = []
                final_vals = []
                casts = []
                
                for col, dtype in pg_cols.items():
                    if col in row_dict:
                        val = row_dict[col]
                        if val == "" or val == "None": val = None
                        
                        # FORCE TYPES
                        if dtype in ('integer', 'bigint', 'smallint'):
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
                            
                        cols_to_use.append(col)
                        final_vals.append(val)
                
                insert_sql = f"INSERT INTO {table} ({','.join(cols_to_use)}) VALUES ({','.join(casts)})"
                pg_cur.execute(insert_sql, final_vals)
            
            pg_conn.commit()
            
            # Verificación Inmediata
            pg_cur.execute(f"SELECT COUNT(*) FROM {table}")
            c = pg_cur.fetchone()[0]
            print(f"    ✓ OK. Conteos: SQLite={len(rows)}, PG={c}")
            
            if table == 'productos' and c > 0:
                pg_cur.execute("SELECT id FROM productos WHERE id=20")
                if pg_cur.fetchone():
                    print("    ✓ ID 20 Verificado.")
                else:
                    print("    ❌ ID 20 NO ENCONTRADO EN PG.")

        # Sincronizar secuencias
        for table in migration_order:
            try:
                pg_cur.execute(f"SELECT pg_get_serial_sequence('{table}', 'id')")
                seq = pg_cur.fetchone()[0]
                if seq:
                    pg_cur.execute(f"SELECT setval('{seq}', (SELECT COALESCE(MAX(id), 1) FROM {table}))")
            except:
                pg_conn.rollback()
        pg_conn.commit()

        print("\n🏆 MIGRACIÓN COMPLETADA EXITOSAMENTE")

    except Exception as e:
        print(f"\n💥 ERROR: {e}")
        if 'pg_conn' in locals(): pg_conn.rollback()
    finally:
        sql_conn.close()
        pg_conn.close()

if __name__ == "__main__":
    migrate()
