import sqlite3
import psycopg2

SQLITE_DB = "backend/instance/elvestuario.db"
POSTGRES_URL = "postgresql://elvestuario_user:IbkOl9uuqKVHSae7WWJ9nPox6mXl9YSC@dpg-d5nqgrngi27c73ea03hg-a.oregon-postgres.render.com/elvestuario"

def migrate_rest():
    sql_conn = sqlite3.connect(SQLITE_DB)
    sql_conn.row_factory = sqlite3.Row
    sql_cur = sql_conn.cursor()
    
    pg_conn = psycopg2.connect(POSTGRES_URL)
    pg_cur = pg_conn.cursor()

    # Tablas restantes
    rest_tables = ['colores', 'talles', 'stock_talles', 'admins', 'clientes', 'pedidos', 'detalles_pedido']

    for table in rest_tables:
        # Schema PG
        pg_cur.execute(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = '{table}'")
        pg_cols = {r[0]: r[1] for r in pg_cur.fetchall()}
        if not pg_cols: continue

        # Data SQLite
        sql_cur.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
        if not sql_cur.fetchone(): continue

        sql_cur.execute(f"SELECT * FROM {table}")
        rows = sql_cur.fetchall()
        print(f"Migrando {table} ({len(rows)} filas)...")

        for row in rows:
            d = dict(row)
            cols = []
            vals = []
            casts = []
            for col, dtype in pg_cols.items():
                if col in d:
                    val = d[col]
                    if val == "" or val == "None": val = None
                    
                    if col == 'id' or col.endswith('_id'):
                        try: val = int(val) if val is not None else None
                        except: val = None
                        casts.append("%s::integer")
                    elif dtype in ('integer', 'bigint'):
                        try: val = int(val) if val is not None else None
                        except: val = None
                        casts.append("%s::integer")
                    elif 'bool' in dtype:
                        val = bool(val) if val is not None else None
                        casts.append("%s::boolean")
                    else:
                        val = str(val) if val is not None else None
                        casts.append("%s")
                    
                    cols.append(col)
                    vals.append(val)

            sql = f"INSERT INTO {table} ({','.join(cols)}) VALUES ({','.join(casts)})"
            try:
                pg_cur.execute(sql, vals)
            except Exception as e:
                print(f"  ❌ Error en {table} (ID {d.get('id')}): {e}")
                pg_conn.rollback()
                return # Abortamos si falla uno para arreglarlo

        pg_conn.commit()
        print(f"  ✓ {table} OK")

    # Sincronizar secuencias
    print("Sincronizando secuencias...")
    pg_cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
    all_tables = [r[0] for r in pg_cur.fetchall()]
    for t in all_tables:
        try:
            pg_cur.execute(f"SELECT pg_get_serial_sequence('{t}', 'id')")
            seq = pg_cur.fetchone()[0]
            if seq:
                pg_cur.execute(f"SELECT setval('{seq}', (SELECT COALESCE(MAX(id), 1) FROM {t}))")
        except:
            pg_conn.rollback()
    pg_conn.commit()
    print("✓ Secuencias sincronizadas.")

    pg_cur.close()
    pg_conn.close()
    sql_conn.close()

migrate_rest()
