import sqlite3
import psycopg2
from psycopg2.extras import execute_values
import os

SQLITE_DB = "backend/instance/elvestuario.db"
POSTGRES_URL = "postgresql://elvestuario_user:IbkOl9uuqKVHSae7WWJ9nPox6mXl9YSC@dpg-d5nqgrngi27c73ea03hg-a.oregon-postgres.render.com/elvestuario"

def clean_val(val, col_name):
    if val == "" or val == "None" or val is None:
        return None
    if col_name.endswith('_id') or col_name == 'id':
        try:
            return int(val)
        except:
            return None # Si no es convertible a int, que sea NULL
    return val

def migrate():
    try:
        sql_conn = sqlite3.connect(SQLITE_DB)
        sql_conn.row_factory = sqlite3.Row
        sql_cur = sql_conn.cursor()
        
        pg_conn = psycopg2.connect(POSTGRES_URL)
        pg_cur = pg_conn.cursor()

        # Inspeccionar tipos en PG
        print("--- Esquema PG Categorías ---")
        pg_cur.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'categorias'
        """)
        for col in pg_cur.fetchall():
            print(f" Column: {col[0]} | Type: {col[1]}")

        # Limpiar
        print("\nLimpiando tablas...")
        pg_cur.execute("TRUNCATE TABLE categorias RESTART IDENTITY CASCADE")
        pg_conn.commit()

        print("Migrando Categorías...")
        sql_cur.execute("SELECT * FROM categorias ORDER BY categoria_padre_id ASC NULLS FIRST")
        rows = sql_cur.fetchall()
        for row in rows:
            cols = list(row.keys())
            vals = [clean_val(row[k], k) for k in cols]
            
            # DEBUG de la primera fila o fallo
            print(f"Insertando: {dict(zip(cols, vals))}")
            
            placeholders = ",".join(["%s"] * len(cols))
            sql = f"INSERT INTO categorias ({','.join(cols)}) VALUES ({placeholders})"
            pg_cur.execute(sql, vals)
            
        pg_conn.commit()
        print("✓ Categorías migradas")

    except Exception as e:
        print(f"❌ ERROR: {e}")
        if 'pg_conn' in locals(): pg_conn.rollback()
    finally:
        if 'sql_conn' in locals(): sql_conn.close()
        if 'pg_conn' in locals(): pg_conn.close()

if __name__ == "__main__":
    migrate()
