"""
Script para ejecutar la migración de índices en stock_talles
"""
import psycopg2
from psycopg2 import sql

# Configuración de conexión (ajustar según tu configuración)
DB_CONFIG = {
    'dbname': 'paglauridb',
    'user': 'postgres',
    'password': 'admin123',  # Ajustar según tu configuración
    'host': 'localhost',
    'port': 5432
}

def run_migration():
    """Ejecutar migración de índices"""
    try:
        # Conectar a la base de datos
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        print("Conectado a la base de datos...")
        
        # Lista de índices a crear
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_stock_producto ON stock_talles(producto_id)",
            "CREATE INDEX IF NOT EXISTS idx_stock_talle ON stock_talles(talle_id)",
            "CREATE INDEX IF NOT EXISTS idx_stock_cantidad ON stock_talles(cantidad)",
            "CREATE INDEX IF NOT EXISTS idx_stock_producto_cantidad ON stock_talles(producto_id, cantidad)"
        ]
        
        # Crear cada índice
        for idx_sql in indexes:
            print(f"\nEjecutando: {idx_sql}")
            cursor.execute(idx_sql)
            print("✓ Índice creado exitosamente")
        
        # Commit de los cambios
        conn.commit()
        print("\n✓ Migración completada exitosamente")
        
        # Verificar índices creados
        print("\n--- Índices en stock_talles ---")
        cursor.execute("""
            SELECT indexname, indexdef
            FROM pg_indexes
            WHERE tablename = 'stock_talles'
            ORDER BY indexname
        """)
        
        for row in cursor.fetchall():
            print(f"  {row[0]}: {row[1]}")
        
        # Cerrar conexión
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        if conn:
            conn.rollback()

if __name__ == "__main__":
    run_migration()
