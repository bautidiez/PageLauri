import sqlite3
import psycopg2
from psycopg2.extras import execute_values
import os

# CONFIGURACIÓN
SQLITE_DB = "backend/instance/elvestuario.db"
# El usuario pasó la interna, intentaremos adivinar la externa o pedirla si falla
# Host interno: dpg-d5nqgrngi27c73ea03hg-a
# Probable host externo: dpg-d5nqgrngi27c73ea03hg-a.ohio-postgres.render.com (depende de la región)
POSTGRES_URL = "postgresql://elvestuario_user:IbkOl9uuqKVHSae7WWJ9nPox6mXl9YSC@dpg-d5nqgrngi27c73ea03hg-a.ohio-postgres.render.com/elvestuario"

def migrate():
    print(f"--- Iniciando Migración ---")
    
    try:
        # 1. Conexiones
        print(f"Conectando a SQLite: {SQLITE_DB}")
        sql_conn = sqlite3.connect(SQLITE_DB)
        sql_conn.row_factory = sqlite3.Row
        sql_cur = sql_conn.cursor()
        
        print(f"Conectando a PostgreSQL...")
        # Reemplazar el host si es necesario
        pg_url = POSTGRES_URL
        # Si falla la conexión externa, lo reportaremos
        try:
            pg_conn = psycopg2.connect(pg_url)
        except Exception as e:
            print(f"Error conexión (Ohio?): {e}")
            print("Probando con Oregon...")
            pg_url = POSTGRES_URL.replace(".ohio-", ".oregon-")
            try:
                pg_conn = psycopg2.connect(pg_url)
            except Exception as e2:
                print(f"Error conexión (Oregon?): {e2}")
                return False
                
        pg_cur = pg_conn.cursor()
        print("✓ Conexiones establecidas")

        # 2. Orden de tablas (Integridad referencial)
        tables = [
            'admins',
            'categorias',
            'colores',
            'talles',
            'productos',
            'stock_talle',
            'clientes',
            'pedidos',
            'detalles_pedido',
            'promociones_producto',
            'promocion_productos_link',
            'promocion_categorias_link'
        ]

        # 3. Limpiar base de datos destino (Opcional pero recomendado para fresh start)
        print("Limpiando tablas en PostgreSQL...")
        for table in reversed(tables):
            try:
                pg_cur.execute(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE;")
            except:
                pg_conn.rollback()
                pg_cur.execute(f"DELETE FROM {table};")
        pg_conn.commit()

        # 4. Migrar Categorías (Necesita orden especial por padres)
        print("Migrando Categorías...")
        sql_cur.execute("SELECT * FROM categorias ORDER BY categoria_padre_id NULLS FIRST, id")
        rows = sql_cur.fetchall()
        for row in rows:
            cols = list(row.keys())
            vals = [row[k] for k in cols]
            placeholders = ",".join(["%s"] * len(cols))
            pg_cur.execute(f"INSERT INTO categorias ({','.join(cols)}) VALUES ({placeholders})", vals)
        pg_conn.commit()
        print(f"✓ {len(rows)} categorías migradas")

        # 5. Migrar el resto de tablas simples
        simple_tables = [t for t in tables if t != 'categorias']
        for table in simple_tables:
            print(f"Migrando {table}...")
            sql_cur.execute(f"SELECT * FROM {table}")
            rows = sql_cur.fetchall()
            if not rows:
                print(f"  (Saliendo: {table} está vacía)")
                continue
            
            cols = list(rows[0].keys())
            placeholders = ",".join(["%s"] * len(cols))
            insert_query = f"INSERT INTO {table} ({','.join(cols)}) VALUES ({placeholders})"
            
            data = [tuple(row[k] for k in cols) for row in rows]
            execute_values(pg_cur, f"INSERT INTO {table} ({','.join(cols)}) VALUES %s", data)
            pg_conn.commit()
            print(f"✓ {len(rows)} filas migradas en {table}")

        print("\n--- MIGRACIÓN COMPLETADA CON ÉXITO ---")
        return True

    except Exception as e:
        print(f"❌ ERROR CRÍTICO: {e}")
        return False
    finally:
        if 'sql_conn' in locals(): sql_conn.close()
        if 'pg_conn' in locals(): pg_conn.close()

if __name__ == "__main__":
    migrate()
