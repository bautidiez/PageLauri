import psycopg2

POSTGRES_URL = "postgresql://elvestuario_user:IbkOl9uuqKVHSae7WWJ9nPox6mXl9YSC@dpg-d5nqgrngi27c73ea03hg-a.oregon-postgres.render.com/elvestuario"

def audit():
    conn = psycopg2.connect(POSTGRES_URL)
    cur = conn.cursor()
    
    cur.execute("SELECT COUNT(*) FROM productos")
    count = cur.fetchone()[0]
    print(f"Total productos en PG: {count}")
    
    if count > 0:
        cur.execute("SELECT id, nombre FROM productos ORDER BY id")
        rows = cur.fetchall()
        ids = [r[0] for r in rows]
        print(f"IDs encontrados (primeros 100): {ids}")
        
        if 20 in ids:
            print("✓ ID 20 EXISTE")
        else:
            print("❌ ID 20 NO EXISTE")
            # Mostrar que hay en el lugar de 20
            cur.execute("SELECT * FROM productos WHERE id > 15 LIMIT 10")
            print(f"Productos > 15: {cur.fetchall()}")

    cur.close()
    conn.close()

audit()
