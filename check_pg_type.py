import psycopg2

POSTGRES_URL = "postgresql://elvestuario_user:IbkOl9uuqKVHSae7WWJ9nPox6mXl9YSC@dpg-d5nqgrngi27c73ea03hg-a.oregon-postgres.render.com/elvestuario"

def check():
    try:
        conn = psycopg2.connect(POSTGRES_URL)
        cur = conn.cursor()
        
        # Check if columns are IDENTITY or SERIAL
        cur.execute("""
            SELECT column_name, is_identity, identity_generation
            FROM information_schema.columns 
            WHERE table_name = 'productos' AND column_name = 'id'
        """)
        res = cur.fetchone()
        print(f"ID Column Info: {res}")
        
        # Try a simple manual insert with a specific ID
        try:
            print("Testing manual insert with ID 999...")
            cur.execute("INSERT INTO productos (id, nombre, categoria_id, precio_base, activo) VALUES (%s, %s, %s, %s, %s)", 
                        (999, 'Test Manual', None, 100, True))
            conn.commit()
            print("✓ Manual insert OK")
        except Exception as e:
            conn.rollback()
            print(f"❌ Manual insert FAILED: {e}")
            
        cur.execute("SELECT id FROM productos WHERE id=999")
        if cur.fetchone():
            print("✓ ID 999 is in DB")
        else:
            print("❌ ID 999 not found after commit")

        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check()
