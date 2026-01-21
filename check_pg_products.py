import psycopg2

POSTGRES_URL = "postgresql://elvestuario_user:IbkOl9uuqKVHSae7WWJ9nPox6mXl9YSC@dpg-d5nqgrngi27c73ea03hg-a.oregon-postgres.render.com/elvestuario"

def check():
    try:
        conn = psycopg2.connect(POSTGRES_URL)
        cur = conn.cursor()
        
        cur.execute("SELECT COUNT(*) FROM productos")
        count = cur.fetchone()[0]
        print(f"Total productos in PG: {count}")
        
        cur.execute("SELECT id, nombre FROM productos ORDER BY id LIMIT 100")
        rows = cur.fetchall()
        print("Product IDs in PG:")
        ids = [r[0] for r in rows]
        print(ids)
        
        if 20 in ids:
            print("✓ ID 20 found!")
        else:
            print("❌ ID 20 MISSING!")
            
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check()
