"""
Script para aplicar migración: agregar columna compra_minima a promociones_productos
"""
import os
import sys
from dotenv import load_dotenv
import psycopg2

# Cargar variables de entorno
load_dotenv()

def apply_migration():
    # Obtener la URL de la base de datos
    db_url = os.getenv('DATABASE_URL')
    
    if not db_url:
        print("ERROR: DATABASE_URL no encontrada en .env")
        return False
    
    # Parsear la URL para psycopg2
    # Formato: postgresql://user:pass@host:port/dbname
    if db_url.startswith('postgresql://'):
        try:
            # Conectar a la base de datos
            conn = psycopg2.connect(db_url)
            cur = conn.cursor()
            
            print("Conectado a la base de datos PostgreSQL")
            
            # Leer el archivo SQL
            with open('migrations/fix_promociones_compra_minima.sql', 'r') as f:
                sql = f.read()
            
            # Ejecutar la migración
            cur.execute(sql)
            conn.commit()
            
            print("✓ Migración aplicada exitosamente: compra_minima agregado a promociones_productos")
            
            # Verificar que la columna existe
            cur.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'promociones_productos' 
                AND column_name = 'compra_minima'
            """)
            result = cur.fetchone()
            
            if result:
                print(f"✓ Columna 'compra_minima' verificada en la tabla")
            else:
                print("⚠ Advertencia: No se pudo verificar la columna")
            
            cur.close()
            conn.close()
            return True
            
        except Exception as e:
            print(f"ERROR al aplicar migración: {e}")
            return False
    else:
        print("Esta migración solo es necesaria para PostgreSQL")
        print(f"Tu base de datos parece ser: {db_url.split(':')[0]}")
        return False

if __name__ == '__main__':
    print("=" * 60)
    print("Aplicando migración: fix_promociones_compra_minima.sql")
    print("=" * 60)
    success = apply_migration()
    sys.exit(0 if success else 1)
