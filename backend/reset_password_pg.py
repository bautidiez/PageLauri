import psycopg2
from werkzeug.security import generate_password_hash

POSTGRES_URL = "postgresql://elvestuario_user:IbkOl9uuqKVHSae7WWJ9nPox6mXl9YSC@dpg-d5nqgrngi27c73ea03hg-a.oregon-postgres.render.com/elvestuario"

def reset_password():
    new_pass = "ElVestuario2024!Admin"
    password_hash = generate_password_hash(new_pass)
    
    try:
        conn = psycopg2.connect(POSTGRES_URL)
        cur = conn.cursor()
        
        # Actualizar la contraseña del usuario 'admin'
        cur.execute("UPDATE admins SET password_hash = %s WHERE username = 'admin'", (password_hash,))
        
        if cur.rowcount == 0:
            # Si no existe, lo creamos
            cur.execute("INSERT INTO admins (username, email, password_hash) VALUES (%s, %s, %s)", 
                        ('admin', 'admin@elvestuario.com', password_hash))
            print("✅ Usuario 'admin' creado con nueva contraseña.")
        else:
            print("✅ Contraseña de 'admin' actualizada correctamente.")
            
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"❌ Error al resetear contraseña: {e}")

if __name__ == "__main__":
    reset_password()
