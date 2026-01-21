"""
Script para resetear la contraseña del admin directamente en producción
Ejecutar con: python reset_admin_production.py
"""
import psycopg2
from werkzeug.security import generate_password_hash
import os

# IMPORTANTE: Configura esta URL con la de tu base de datos de Render
# La encuentras en: Render Dashboard > PostgreSQL > Internal Database URL
DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://...')

# La nueva contraseña que quieres establecer
NUEVA_PASSWORD = 'ElVestuario2024!Admin'

def reset_admin_password():
    """Resetea la contraseña del admin en la base de datos de producción"""
    try:
        # Conectar a la base de datos
        print("🔄 Conectando a la base de datos de producción...")
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # Generar el hash de la nueva contraseña
        password_hash = generate_password_hash(NUEVA_PASSWORD)
        print(f"✓ Hash generado correctamente (longitud: {len(password_hash)})")
        
        # Actualizar la contraseña del admin
        cursor.execute(
            "UPDATE admin SET password_hash = %s WHERE username = 'admin'",
            (password_hash,)
        )
        
        # Confirmar los cambios
        conn.commit()
        
        # Verificar que se actualizó
        cursor.execute("SELECT username, email FROM admin WHERE username = 'admin'")
        admin = cursor.fetchone()
        
        if admin:
            print(f"✓ Contraseña actualizada exitosamente para: {admin[0]} ({admin[1]})")
            print(f"✓ Nueva contraseña: {NUEVA_PASSWORD}")
            print(f"✓ Longitud: {len(NUEVA_PASSWORD)} caracteres")
        else:
            print("❌ No se encontró el usuario admin")
        
        cursor.close()
        conn.close()
        print("\n✓ Proceso completado. Intenta hacer login ahora.")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\nAsegúrate de:")
        print("1. Tener instalado psycopg2: pip install psycopg2-binary")
        print("2. Configurar DATABASE_URL con la URL de tu base de datos de Render")

if __name__ == "__main__":
    print("=" * 60)
    print("🔐 RESETEO DE CONTRASEÑA DE ADMIN EN PRODUCCIÓN")
    print("=" * 60)
    print(f"Database URL configurada: {DATABASE_URL[:30]}...")
    print(f"Nueva contraseña: {NUEVA_PASSWORD}")
    print("=" * 60)
    
    confirm = input("\n¿Estás seguro de continuar? (escribe 'SI' para confirmar): ")
    
    if confirm.strip().upper() == 'SI':
        reset_admin_password()
    else:
        print("❌ Operación cancelada")
