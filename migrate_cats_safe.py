import sqlite3
import psycopg2
from psycopg2.extras import execute_values
import os

SQLITE_DB = "backend/instance/elvestuario.db"
POSTGRES_URL = "postgresql://elvestuario_user:IbkOl9uuqKVHSae7WWJ9nPox6mXl9YSC@dpg-d5nqgrngi27c73ea03hg-a.oregon-postgres.render.com/elvestuario"

def migrate():
    try:
        sql_conn = sqlite3.connect(SQLITE_DB)
        sql_conn.row_factory = sqlite3.Row
        sql_cur = sql_conn.cursor()
        
        pg_conn = psycopg2.connect(POSTGRES_URL)
        pg_cur = pg_conn.cursor()

        # 1. Obtener columnas válidas de PG para evitar fallos por columnas extra en SQLite
        pg_cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'categorias'")
        pg_cols = {row[0]: row[1] for row in pg_cur.fetchall()}
        print(f"Columnas en PG: {list(pg_cols.keys())}")

        # 2. Limpiar
        pg_cur.execute("TRUNCATE TABLE categorias RESTART IDENTITY CASCADE")
        pg_conn.commit()

        # 3. Migrar ordenadamente
        sql_cur.execute("SELECT * FROM categorias ORDER BY categoria_padre_id ASC NULLS FIRST, id ASC")
        rows = sql_cur.fetchall()
        
        for row in rows:
            # Solo usar columnas que existan en PG
            valid_data = {}
            for col in pg_cols.keys():
                if col in row.keys():
                    val = row[col]
                    # Limpieza agresiva de tipos
                    if val == "" or val == "None" or val is None:
                        valid_data[col] = None
                    elif pg_cols[col] == 'integer' or pg_cols[col] == 'bigint':
                        try:
                            valid_data[col] = int(val)
                        except:
                            valid_data[col] = None
                    else:
                        valid_data[col] = str(val)
                else:
                    valid_data[col] = None # Columna existe en PG pero no en SQLite
            
            cols = list(valid_data.keys())
            vals = [valid_data[c] for c in cols]
            
            placeholders = ",".join(["%s"] * len(cols))
            insert_sql = f"INSERT INTO categorias ({','.join(cols)}) VALUES ({placeholders})"
            
            try:
                pg_cur.execute(insert_sql, vals)
            except Exception as e:
                print(f"Error insertando categoría {valid_data.get('nombre')}: {e}")
                print(f"Valores: {vals}")
                raise e
                
        pg_conn.commit()
        print(f"✓ {len(rows)} categorías migradas correctamente.")

    except Exception as e:
        print(f"❌ ERROR: {e}")
        if 'pg_conn' in locals(): pg_conn.rollback()
    finally:
        if 'sql_conn' in locals(): sql_conn.close()
        if 'pg_conn' in locals(): pg_conn.close()

if __name__ == "__main__":
    migrate()
