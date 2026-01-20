"""
Script de migración para agregar campos de aprobación a pedidos (PostgreSQL)
Ejecutar: python migrations/add_approval_fields_postgres.py
"""
import sys
import os
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
    
    if not db_url.startswith('postgresql://'):
        print("Esta migración solo es para PostgreSQL")
        return False
    
    try:
        # Conectar a la base de datos
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        
        print("=== Conectado a PostgreSQL ===\n")
        
        # Verificar columnas existentes
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'pedidos'
        """)
        existing_columns = [row[0] for row in cur.fetchall()]
        print(f"Columnas existentes en pedidos: {', '.join(existing_columns)}\n")
        
        # Agregar columna 'aprobado' si no existe
        if 'aprobado' not in existing_columns:
            print("Agregando columna 'aprobado'...")
            cur.execute("""
                ALTER TABLE pedidos 
                ADD COLUMN aprobado BOOLEAN DEFAULT FALSE NOT NULL
            """)
            conn.commit()
            print("✓ Columna 'aprobado' agregada\n")
        else:
            print("✓ Columna 'aprobado' ya existe\n")
        
        # Agregar columna 'fecha_expiracion' si no existe
        if 'fecha_expiracion' not in existing_columns:
            print("Agregando columna 'fecha_expiracion'...")
            cur.execute("""
                ALTER TABLE pedidos 
                ADD COLUMN fecha_expiracion TIMESTAMP
            """)
            conn.commit()
            print("✓ Columna 'fecha_expiracion' agregada\n")
        else:
            print("✓ Columna 'fecha_expiracion' ya existe\n")
        
        # Agregar columna 'fecha_aprobacion' si no existe
        if 'fecha_aprobacion' not in existing_columns:
            print("Agregando columna 'fecha_aprobacion'...")
            cur.execute("""
                ALTER TABLE pedidos 
                ADD COLUMN fecha_aprobacion TIMESTAMP
            """)
            conn.commit()
            print("✓ Columna 'fecha_aprobacion' agregada\n")
        else:
            print("✓ Columna 'fecha_aprobacion' ya existe\n")
        
        # Agregar columna 'admin_aprobador_id' si no existe
        if 'admin_aprobador_id' not in existing_columns:
            print("Agregando columna 'admin_aprobador_id'...")
            cur.execute("""
                ALTER TABLE pedidos 
                ADD COLUMN admin_aprobador_id INTEGER REFERENCES admins(id)
            """)
            conn.commit()
            print("✓ Columna 'admin_aprobador_id' agregada\n")
        else:
            print("✓ Columna 'admin_aprobador_id' ya existe\n")
        
        # Actualizar pedidos existentes
        print("Actualizando pedidos existentes...")
        
        # Pedidos que NO están como 'pendiente' o 'pendiente_aprobacion' se marcan como aprobados
        cur.execute("""
            UPDATE pedidos 
            SET aprobado = TRUE, 
                fecha_aprobacion = created_at
            WHERE estado NOT IN ('pendiente', 'pendiente_aprobacion')
            AND aprobado = FALSE
        """)
        count_aprobados = cur.rowcount
        conn.commit()
        print(f"✓ {count_aprobados} pedidos marcados como aprobados\n")
        
        # Pedidos pendientes: set fecha_expiracion
        cur.execute("""
            UPDATE pedidos 
            SET fecha_expiracion = created_at + INTERVAL '5 days',
                estado = 'pendiente_aprobacion'
            WHERE estado IN ('pendiente', 'pendiente_aprobacion')
            AND fecha_expiracion IS NULL
        """)
        count_pendientes = cur.rowcount
        conn.commit()
        print(f"✓ {count_pendientes} pedidos pendientes configurados con fecha de expiración\n")
        
        # Crear índices si no existen
        print("Creando índices...")
        
        # Verificar si los índices ya existen
        cur.execute("""
            SELECT indexname 
            FROM pg_indexes 
            WHERE tablename = 'pedidos'
        """)
        existing_indexes = [row[0] for row in cur.fetchall()]
        
        if 'idx_pedido_aprobado' not in existing_indexes:
            cur.execute("CREATE INDEX idx_pedido_aprobado ON pedidos(aprobado)")
            conn.commit()
            print("✓ Índice 'idx_pedido_aprobado' creado")
        
        if 'idx_pedido_estado_aprobado' not in existing_indexes:
            cur.execute("CREATE INDEX idx_pedido_estado_aprobado ON pedidos(estado, aprobado)")
            conn.commit()
            print("✓ Índice 'idx_pedido_estado_aprobado' creado")
        
        print("\n" + "="*60)
        print("✅ MIGRACIÓN COMPLETADA EXITOSAMENTE")
        print("="*60)
        print(f"   - {count_aprobados} pedidos marcados como aprobados")
        print(f"   - {count_pendientes} pedidos pendientes configurados")
        
        cur.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR al aplicar migración: {e}")
        if 'conn' in locals():
            conn.rollback()
        return False

if __name__ == '__main__':
    print("="*60)
    print("MIGRACIÓN: Agregar campos de aprobación a pedidos")
    print("="*60 + "\n")
    success = apply_migration()
    sys.exit(0 if success else 1)
