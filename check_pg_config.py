import psycopg2

POSTGRES_URL = "postgresql://elvestuario_user:IbkOl9uuqKVHSae7WWJ9nPox6mXl9YSC@dpg-d5nqgrngi27c73ea03hg-a.oregon-postgres.render.com/elvestuario"

def check():
    conn = psycopg2.connect(POSTGRES_URL)
    cur = conn.cursor()
    cur.execute("""
        SELECT column_name, is_identity, identity_generation, column_default 
        FROM information_schema.columns 
        WHERE table_name = 'productos' AND column_name = 'id'
    """)
    res = cur.fetchone()
    print(f"Productos ID: {res}")
    
    cur.execute("SELECT COUNT(*) FROM productos")
    print(f"Productos Count: {cur.fetchone()[0]}")
    
    cur.close()
    conn.close()

check()
