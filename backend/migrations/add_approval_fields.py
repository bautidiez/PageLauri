"""
Script de migración para agregar campos de aprobación a pedidos
Ejecutar: python migrations/add_approval_fields.py
"""
import sys
import os

# Agregar el directorio padre al path para importar módulos
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import db, Pedido
from datetime import datetime, timedelta
from sqlalchemy import text

def migrate():
    # Importar app aquí para evitar problemas de importación circular
    import run
    app = run.app
    
    with app.app_context():
        print("=== Iniciando migración: Agregar campos de aprobación ===")
        
        # 1. Agregar columnas si no existen
        try:
            with db.engine.connect() as conn:
                # Verificar si las columnas ya existen
                result = conn.execute(text("PRAGMA table_info(pedidos)"))
                columns = [row[1] for row in result]
                
                if 'aprobado' not in columns:
                    print("Agregando columna 'aprobado'...")
                    conn.execute(text("ALTER TABLE pedidos ADD COLUMN aprobado BOOLEAN DEFAULT 0 NOT NULL"))
                    conn.commit()
                else:
                    print("Columna 'aprobado' ya existe")
                
                if 'fecha_expiracion' not in columns:
                    print("Agregando columna 'fecha_expiracion'...")
                    conn.execute(text("ALTER TABLE pedidos ADD COLUMN fecha_expiracion DATETIME"))
                    conn.commit()
                else:
                    print("Columna 'fecha_expiracion' ya existe")
                
                if 'fecha_aprobacion' not in columns:
                    print("Agregando columna 'fecha_aprobacion'...")
                    conn.execute(text("ALTER TABLE pedidos ADD COLUMN fecha_aprobacion DATETIME"))
                    conn.commit()
                else:
                    print("Columna 'fecha_aprobacion' ya existe")
                
                if 'admin_aprobador_id' not in columns:
                    print("Agregando columna 'admin_aprobador_id'...")
                    conn.execute(text("ALTER TABLE pedidos ADD COLUMN admin_aprobador_id INTEGER"))
                    conn.commit()
                else:
                    print("Columna 'admin_aprobador_id' ya existe")
                    
        except Exception as e:
            print(f"Error agregando columnas: {e}")
            return
        
        # 2. Actualizar pedidos existentes
        print("\nActualizando pedidos existentes...")
        
        # Pedidos que NO están como 'pendiente' o 'pendiente_aprobacion' se marcan como aprobados
        pedidos_a_aprobar = Pedido.query.filter(
            Pedido.estado.notin_(['pendiente', 'pendiente_aprobacion'])
        ).all()
        
        count_aprobados = 0
        for pedido in pedidos_a_aprobar:
            pedido.aprobado = True
            pedido.fecha_aprobacion = pedido.created_at  # Asumir aprobado al crearlos
            count_aprobados += 1
        
        print(f"Marcados como aprobados: {count_aprobados} pedidos")
        
        # Pedidos pendientes: set fecha_expiracion y mantener aprobado=False
        pedidos_pendientes = Pedido.query.filter(
            Pedido.estado.in_(['pendiente', 'pendiente_aprobacion'])
        ).all()
        
        count_pendientes = 0
        for pedido in pedidos_pendientes:
            if not pedido.fecha_expiracion:
                pedido.fecha_expiracion = pedido.created_at + timedelta(days=5)
                pedido.estado = 'pendiente_aprobacion'
                count_pendientes += 1
        
        print(f"Configurados con fecha de expiración: {count_pendientes} pedidos pendientes")
        
        # 3. Guardar cambios
        try:
            db.session.commit()
            print("\n✅ Migración completada exitosamente")
            print(f"   - {count_aprobados} pedidos marcados como aprobados")
            print(f"   - {count_pendientes} pedidos pendientes configurados")
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Error al guardar cambios: {e}")
            
if __name__ == '__main__':
    migrate()
