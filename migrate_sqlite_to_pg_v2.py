import sqlite3
import psycopg2
from psycopg2.extras import execute_values
import os

# CONFIGURACIÓN
SQLITE_DB = "backend/instance/elvestuario.db"
BASE_URL = "postgresql://elvestuario_user:IbkOl9uuqKVHSae7WWJ9nPox6mXl9YSC@{host}/elvestuario"

def test_connection():
    internal_host = "dpg-d5nqgrngi27c73ea03hg-a"
    possible_hosts = [
        f"{internal_host}.oregon-postgres.render.com",
        f"{internal_host}.ohio-postgres.render.com",
        f"{internal_host}.frankfurt-postgres.render.com",
        f"{internal_host}.singapore-postgres.render.com"
    ]
    
    valid_url = None
    for host in possible_hosts:
        url = BASE_URL.format(host=host)
        print(f"Probando {host}...")
        try:
            conn = psycopg2.connect(url, connect_timeout=5)
            print(f"✓ ÉXITO: {host} es accesible.")
            conn.close()
            valid_url = url
            break
        except Exception as e:
            print(f"  Falló: {e}")
            
    if not valid_url:
        print("\n❌ No se pudo conectar a ninguna URL externa.")
        print("Por favor, verifica en Render Dashboard la 'External Database URL'.")
        return None
    return valid_url

def migrate(pg_url):
    print(f"\n--- Iniciando Migración a {pg_url.split('@')[1].split('/')[0]} ---")
    
    try:
        sql_conn = sqlite3.connect(SQLITE_DB)
        sql_conn.row_factory = sqlite3.Row
        sql_cur = sql_conn.cursor()
        
        pg_conn = psycopg2.connect(pg_url)
        pg_cur = pg_conn.cursor()

        # Tablas en orden (basado en models.py y dependencias)
        tables = [
            'admins',
            'categorias',
            'colores',
            'talles',
            'productos',
            'stock_talles', # Note 'stock_talles' instead of 'stock_talle'
            'clientes',
            'pedidos',
            'detalles_pedido',
            'promociones_producto',
            'promocion_productos_link',
            'promocion_categorias_link'
        ]

        # Limpiar
        print("Limpiando tablas en PostgreSQL (TRUNCATE CASCADE)...")
        for table in reversed(tables):
            try:
                pg_cur.execute(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE;")
            except Exception as e:
                pg_conn.rollback()
                print(f"  Nota: No se pudo truncar {table}, intentando DELETE: {e}")
                try:
                    pg_cur.execute(f"DELETE FROM {table};")
                except:
                    pg_conn.rollback()
                    print(f"  Error: La tabla {table} quizás no existe aún.")
        pg_conn.commit()

        # Especial: Categorías (Recursivo)
        print("Migrando Categorías...")
        sql_cur.execute("SELECT * FROM categorias ORDER BY categoria_padre_id ASC NULLS FIRST, id ASC")
        rows = sql_cur.fetchall()
        for row in rows:
            cols = list(row.keys())
            vals = [row[k] for k in cols]
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
            data = [tuple(row[k] for k in cols) for row in rows]
            
            # Use execute_values for performance
            execute_values(pg_cur, f"INSERT INTO {table} ({','.join(cols)}) VALUES %s", data)
            pg_conn.commit()
            print(f"✓ {len(rows)} filas migradas")

        print("\n🏆 MIGRACIÓN COMPLETADA CON ÉXITO")
        return True

    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

if __name__ == "__main__":
    valid_url = test_connection()
    if valid_url:
        migrate(valid_url)
