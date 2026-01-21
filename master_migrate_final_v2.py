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

        tables = [
            'colores', 'talles', 'categorias', 'productos', 
            'stock_talle', 'stock_talles', 'admins', 
            'clientes', 'pedidos', 'detalles_pedido', 
            'promociones_producto', 'promocion_productos_link', 'promocion_categorias_link'
        ]

        print("--- Limpieza ---")
        pg_cur.execute("TRUNCATE TABLE stock_talles, stock_talle, detalles_pedido, pedidos, productos, categorias, talles, colores, promocion_productos_link, promocion_categorias_link, promociones_producto, clientes, admins RESTART IDENTITY CASCADE")
        pg_conn.commit()
        print("✓ Limpieza completada.")

        for table in tables:
            # Check PG schema
            pg_cur.execute(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = '{table}'")
            pg_cols = {r[0]: r[1] for r in pg_cur.fetchall()}
            if not pg_cols: continue

            # Check SQLite
            sql_cur.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
            if not sql_cur.fetchone(): continue

            sql_cur.execute(f"SELECT * FROM {table} " + ("ORDER BY categoria_padre_id ASC NULLS FIRST" if table == 'categorias' else ""))
            rows = sql_cur.fetchall()
            print(f"Subiendo {table} ({len(rows)} filas)...")

            for row in rows:
                row_dict = dict(row)
                cols_to_insert = []
                values = []
                for col, dtype in pg_cols.items():
                    if col in row_dict:
                        val = row_dict[col]
                        if val == "" or val == "None": val = None
                        cols_to_insert.append(col)
                        values.append(val)
                
                placeholders = ",".join(["%s"] * len(cols_to_insert))
                sql = f"INSERT INTO {table} ({','.join(cols_to_insert)}) VALUES ({placeholders})"
                pg_cur.execute(sql, values)
            
            pg_conn.commit()
            
            # Verificación
            pg_cur.execute(f"SELECT COUNT(*) FROM {table}")
            count = pg_cur.fetchone()[0]
            print(f"    ✓ OK. Total en PG: {count}")
            
            if table == 'productos':
                # Double check ID 20
                pg_cur.execute("SELECT id FROM productos WHERE id=20")
                if not pg_cur.fetchone():
                    print("    ⚠️ ADVERTENCIA: ID 20 no se encuentra en productos después del commit!")
                    pg_cur.execute("SELECT id FROM productos ORDER BY id ASC")
                    print(f"    IDs actuales: {[r[0] for r in pg_cur.fetchall()]}")

        # Sincronizar secuencias
        print("\n--- Sincronizando Secuencias ---")
        for table in tables:
            try:
                pg_cur.execute(f"SELECT pg_get_serial_sequence('{table}', 'id')")
                seq = pg_cur.fetchone()[0]
                if seq:
                    pg_cur.execute(f"SELECT setval('{seq}', (SELECT COALESCE(MAX(id), 1) FROM {table}))")
                    print(f"✓ {seq} sincronizada.")
            except:
                pg_conn.rollback()

        pg_conn.commit()
        print("\n🚀 ¡MIGRACIÓN EXITOSA!")

    except Exception as e:
        print(f"❌ FALLO: {e}")
        if 'pg_conn' in locals(): pg_conn.rollback()
    finally:
        sql_conn.close()
        pg_conn.close()

if __name__ == "__main__":
    migrate()
