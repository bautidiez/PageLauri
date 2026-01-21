import sqlite3
import psycopg2
from psycopg2.extras import execute_values
import os

# CONFIGURACIÓN
SQLITE_DB = "backend/instance/elvestuario.db"
# Ya sabemos que es Oregon
POSTGRES_URL = "postgresql://elvestuario_user:IbkOl9uuqKVHSae7WWJ9nPox6mXl9YSC@dpg-d5nqgrngi27c73ea03hg-a.oregon-postgres.render.com/elvestuario"

def clean_val(val, col_name=None):
    """Limpia valores para que sean compatibles con PostgreSQL"""
    if val == "" or val == "None" or val is None:
        return None
    # Forzar enteros para IDs si parecen números
    if col_name and (col_name.endswith('_id') or col_name == 'id'):
        try:
            return int(val)
        except:
            return val
    return val

def migrate():
    pg_url = POSTGRES_URL
    print(f"\n--- Iniciando Migración a {pg_url.split('@')[1].split('/')[0]} ---")
    
    try:
        sql_conn = sqlite3.connect(SQLITE_DB)
        sql_conn.row_factory = sqlite3.Row
        sql_cur = sql_conn.cursor()
        
        pg_conn = psycopg2.connect(pg_url)
        pg_cur = pg_conn.cursor()

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

        print("Limpiando tablas en PostgreSQL...")
        for table in reversed(tables):
            try:
                pg_cur.execute(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE;")
            except Exception as e:
                pg_conn.rollback()
                try:
                    pg_cur.execute(f"DELETE FROM {table};")
                except:
                    pg_conn.rollback()
        pg_conn.commit()

        # Categorías con orden jerárquico
        print("Migrando Categorías...")
        sql_cur.execute("SELECT * FROM categorias ORDER BY categoria_padre_id ASC NULLS FIRST")
        rows = sql_cur.fetchall()
        for row in rows:
            cols = list(row.keys())
            vals = [clean_val(row[k], k) for k in cols]
            placeholders = ",".join(["%s"] * len(cols))
            pg_cur.execute(f"INSERT INTO categorias ({','.join(cols)}) VALUES ({placeholders})", vals)
        pg_conn.commit()
        print(f"✓ {len(rows)} categorías migradas")

        # Resto de tablas
        for table in tables:
            if table == 'categorias': continue
            print(f"Migrando {table}...")
            sql_cur.execute(f"SELECT * FROM {table}")
            rows = sql_cur.fetchall()
            if not rows: continue
            
            cols = list(rows[0].keys())
            # Limpiar todos los datos antes de execute_values
            data = []
            for row in rows:
                data.append(tuple(clean_val(row[k], k) for k in cols))
            
            execute_values(pg_cur, f"INSERT INTO {table} ({','.join(cols)}) VALUES %s", data)
            pg_conn.commit()
            print(f"✓ {len(rows)} filas migradas")

        print("\n🏆 MIGRACIÓN COMPLETADA CON ÉXITO")
        return True

    except Exception as e:
        print(f"❌ ERROR: {e}")
        pg_conn.rollback()
        return False
    finally:
        if 'sql_conn' in locals(): sql_conn.close()
        if 'pg_conn' in locals(): pg_conn.close()

if __name__ == "__main__":
    migrate()
