import sqlite3
import psycopg2
import sys

# CONFIGURACIÓN
SQLITE_DB = "backend/instance/elvestuario.db"
# El host externo es Oregon dpg-d5nqgrngi27c73ea03hg-a.oregon-postgres.render.com
POSTGRES_URL = "postgresql://elvestuario_user:IbkOl9uuqKVHSae7WWJ9nPox6mXl9YSC@dpg-d5nqgrngi27c73ea03hg-a.oregon-postgres.render.com/elvestuario"

def migrate_all():
    print("--- INICIANDO MIGRACIÓN DEFINITIVA ---")
    try:
        sql_conn = sqlite3.connect(SQLITE_DB)
        sql_conn.row_factory = sqlite3.Row
        sql_cur = sql_conn.cursor()

        pg_conn = psycopg2.connect(POSTGRES_URL)
        pg_cur = pg_conn.cursor()

        # 1. Obtener tablas existentes en PG
        pg_cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
        pg_tables = [r[0] for r in pg_cur.fetchall()]
        print(f"Tablas en PG: {pg_tables}")

        # Orden de migración para respetar FKs
        tables_to_migrate = [
            'colores', 
            'talles', 
            'categorias', 
            'productos', 
            'stock_talles', # Plural en models.py __tablename__ = 'stock_talles'
            'admins', 
            'clientes', 
            'pedidos', 
            'detalles_pedido',
            'promociones_producto' # Si existe
        ]

        # 2. Limpieza total con CASCADE
        print("\n--- PASO 1: Vaciando tablas en producción ---")
        existing_ordered = [t for t in reversed(tables_to_migrate) if t in pg_tables]
        if existing_ordered:
            try:
                pg_cur.execute(f"TRUNCATE TABLE {','.join(existing_ordered)} RESTART IDENTITY CASCADE;")
                pg_conn.commit()
                print("✓ Tablas vaciadas (Truncate Cascade)")
            except Exception as e:
                pg_conn.rollback()
                print(f"⚠️ Error en Truncate: {e}. Intentando borrado individual...")
                for t in existing_ordered:
                    try:
                        pg_cur.execute(f"DELETE FROM {t};")
                        print(f"  ✓ {t} borrada")
                    except:
                        pg_conn.rollback()
                pg_conn.commit()

        # 3. Migración uno a uno
        print("\n--- PASO 2: Migrando datos ---")
        for table in tables_to_migrate:
            if table not in pg_tables:
                print(f"⚠️ Saltando {table} (No existe en PG)")
                continue

            # Obtener columnas de PG para mapeo exacto
            pg_cur.execute(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = '{table}'")
            pg_cols_info = {r[0]: r[1] for r in pg_cur.fetchall()}
            
            # Leer SQLite
            sql_cur.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
            if not sql_cur.fetchone():
                print(f"⚠️ Saltando {table} (No existe en SQLite)")
                continue

            # Ordenar categorías para padres primero
            query = f"SELECT * FROM {table}"
            if table == 'categorias':
                query += " ORDER BY categoria_padre_id ASC NULLS FIRST, id ASC"
            
            sql_cur.execute(query)
            rows = sql_cur.fetchall()
            print(f"  Migrando {table} ({len(rows)} filas)...")

            for row in rows:
                row_dict = dict(row)
                cols_to_insert = []
                values = []
                placeholders = []

                for col, dtype in pg_cols_info.items():
                    if col in row_dict:
                        val = row_dict[col]
                        if val == "" or val == "None":
                            val = None
                        
                        # Limpieza y casting
                        if val is not None:
                            if dtype in ('integer', 'bigint', 'smallint'):
                                val = int(val)
                                placeholders.append("%s::integer")
                            elif 'numeric' in dtype or 'double' in dtype or 'real' in dtype:
                                val = float(val)
                                placeholders.append("%s::numeric")
                            elif 'bool' in dtype:
                                val = bool(val)
                                placeholders.append("%s::boolean")
                            else:
                                val = str(val)
                                placeholders.append("%s")
                        else:
                            placeholders.append("%s")

                        cols_to_insert.append(col)
                        values.append(val)

                if not cols_to_insert:
                    continue

                insert_sql = f"INSERT INTO {table} ({','.join(cols_to_insert)}) VALUES ({','.join(placeholders)})"
                try:
                    pg_cur.execute(insert_sql, values)
                except Exception as e:
                    print(f"  ❌ Error en {table} (ID {row_dict.get('id')}): {e}")
                    # print(f"  SQL: {insert_sql}")
                    # print(f"  Values: {values}")
                    pg_conn.rollback()
                    raise e
            
            pg_conn.commit()
            print(f"    ✓ OK.")

        # 4. Sincronizar secuencias
        print("\n--- PASO 3: Sincronizando secuencias ---")
        for table in tables_to_migrate:
            if table not in pg_tables: continue
            try:
                pg_cur.execute(f"SELECT pg_get_serial_sequence('{table}', 'id')")
                seq = pg_cur.fetchone()[0]
                if seq:
                    pg_cur.execute(f"SELECT setval('{seq}', (SELECT COALESCE(MAX(id), 1) FROM {table}))")
                    print(f"  ✓ {table} sync OK")
            except:
                pg_conn.rollback()
        pg_conn.commit()

        print("\n🏆 MIGRACIÓN COMPLETADA EXITOSAMENTE")
        print("Total productos migrados:", end=" ")
        pg_cur.execute("SELECT COUNT(*) FROM productos")
        print(pg_cur.fetchone()[0])

    except Exception as e:
        print(f"\n💥 FALLO CRÍTICO EN MIGRACIÓN: {e}")
        if 'pg_conn' in locals(): pg_conn.rollback()
    finally:
        if 'sql_conn' in locals(): sql_conn.close()
        if 'pg_conn' in locals(): pg_conn.close()

if __name__ == "__main__":
    migrate_all()
