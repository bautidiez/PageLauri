import sqlite3
import psycopg2
import sys

# CONFIG
SQLITE_DB = "backend/instance/elvestuario.db"
POSTGRES_URL = "postgresql://elvestuario_user:IbkOl9uuqKVHSae7WWJ9nPox6mXl9YSC@dpg-d5nqgrngi27c73ea03hg-a.oregon-postgres.render.com/elvestuario"

def migrate():
    print("🚀 INICIANDO MIGRACIÓN DE RESCATE (75 productos)")
    try:
        # SQLite
        sql_conn = sqlite3.connect(SQLITE_DB)
        sql_conn.row_factory = sqlite3.Row
        sql_cur = sql_conn.cursor()

        # Postgres
        pg_conn = psycopg2.connect(POSTGRES_URL)
        pg_cur = pg_conn.cursor()

        # 0. Descubrir tablas reales
        pg_cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
        pg_tables = [r[0] for r in pg_cur.fetchall()]
        print(f"Tablas encontradas en PG: {pg_tables}")

        # Orden de migración
        target_tables = [
            'colores', 'talles', 'categorias', 'productos', 
            'stock_talle', 'stock_talles', 'admins', 
            'clientes', 'pedidos', 'detalles_pedido'
        ]

        # 1. Limpieza total ( CASCADE para no tener errores de FK)
        print("\n--- PASO 1: Limpieza ---")
        clean_list = [t for t in reversed(target_tables) if t in pg_tables]
        if clean_list:
            pg_cur.execute(f"TRUNCATE TABLE {','.join(clean_list)} RESTART IDENTITY CASCADE;")
            pg_conn.commit()
            print(f"✓ {len(clean_list)} tablas vaciadas.")

        # 2. Migración
        print("\n--- PASO 2: Carga de Datos ---")
        for table in target_tables:
            if table not in pg_tables: continue
            
            # Verificar si SQLite tiene la tabla
            sql_cur.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
            if not sql_cur.fetchone(): continue

            # Esquema PG
            pg_cur.execute(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = '{table}'")
            pg_cols_info = {r[0]: r[1] for r in pg_cur.fetchall()}

            # Datos SQLite
            query = f"SELECT * FROM {table}"
            if table == 'categorias':
                query += " ORDER BY categoria_padre_id ASC NULLS FIRST, id ASC"
            
            sql_cur.execute(query)
            rows = sql_cur.fetchall()
            if not rows:
                print(f"  - {table}: 0 filas (saltando)")
                continue

            print(f"  - Migrando {table} ({len(rows)} filas)...")
            
            for row in rows:
                d = dict(row)
                cols_to_ins = []
                placeholders = []
                values = []
                
                for col, dtype in pg_cols_info.items():
                    if col in d:
                        val = d[col]
                        # Limpieza
                        if val == "" or val == "None" or val is None:
                            val = None
                        
                        # Type matching
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
                        
                        cols_to_ins.append(col)
                        values.append(val)
                
                sql = f"INSERT INTO {table} ({','.join(cols_to_ins)}) VALUES ({','.join(placeholders)})"
                try:
                    pg_cur.execute(sql, values)
                except Exception as e:
                    print(f"    ❌ Error en {table} (ID {d.get('id')}): {e}")
                    print(f"    Valores: {values}")
                    pg_conn.rollback()
                    return False

            pg_conn.commit()
            print(f"    ✓ OK. {table} migrada.")

        # 3. Sincronizar secuencias
        print("\n--- PASO 3: Sincronización ---")
        for table in target_tables:
            if table not in pg_tables: continue
            try:
                pg_cur.execute(f"SELECT pg_get_serial_sequence('{table}', 'id')")
                seq = pg_cur.fetchone()[0]
                if seq:
                    pg_cur.execute(f"SELECT setval('{seq}', (SELECT COALESCE(MAX(id), 1) FROM {table}))")
            except:
                pg_conn.rollback()
        pg_conn.commit()

        # Validación Final
        pg_cur.execute("SELECT COUNT(*) FROM productos")
        p_count = pg_cur.fetchone()[0]
        print(f"\n🏆 MIGRACIÓN COMPLETADA. Productos en Producción: {p_count}")
        return True

    except Exception as e:
        print(f"\n💥 ERROR CRÍTICO: {e}")
        return False
    finally:
        sql_conn.close()
        pg_conn.close()

if __name__ == "__main__":
    migrate()
