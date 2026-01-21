import sqlite3
import psycopg2

SQLITE_DB = "backend/instance/elvestuario.db"
POSTGRES_URL = "postgresql://elvestuario_user:IbkOl9uuqKVHSae7WWJ9nPox6mXl9YSC@dpg-d5nqgrngi27c73ea03hg-a.oregon-postgres.render.com/elvestuario"

def migrate_config():
    sql_conn = sqlite3.connect(SQLITE_DB)
    sql_conn.row_factory = sqlite3.Row
    sql_cur = sql_conn.cursor()
    
    pg_conn = psycopg2.connect(POSTGRES_URL)
    pg_cur = pg_conn.cursor()

    tables = ['tipos_promocion', 'metodos_pago']

    for table in tables:
        # Schema PG
        pg_cur.execute(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = '{table}'")
        pg_cols = {r[0]: r[1] for r in pg_cur.fetchall()}
        if not pg_cols:
            print(f"⚠️ Tabla {table} no existe en PG.")
            continue

        print(f"Migrando {table}...")
        
        # TRUNCATE
        try:
            pg_cur.execute(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE;")
            pg_conn.commit()
        except:
            pg_conn.rollback()

        sql_cur.execute(f"SELECT * FROM {table}")
        rows = sql_cur.fetchall()
        print(f"  {len(rows)} filas.")

        for row in rows:
            d = dict(row)
            cols = []
            vals = []
            casts = []
            for col, dtype in pg_cols.items():
                if col in d:
                    val = d[col]
                    if val == "" or val == "None": val = None
                    if col == 'id' or col.endswith('_id') or dtype in ('integer', 'bigint'):
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
            pg_cur.execute(sql, vals)
        
        pg_conn.commit()
        print(f"  ✓ {table} OK")
    
    pg_cur.close()
    pg_conn.close()
    sql_conn.close()

migrate_config()
