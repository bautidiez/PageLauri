import os
import sys

# Agregar el directorio actual al path para importar app
sys.path.append(os.getcwd())

from app import app
from models import db, Producto

def test_product_update():
    with app.app_context():
        print("--- INICIANDO DIAGNÓSTICO UPDATE PRODUCTO 2 ---")
        
        try:
            # 1. Buscar producto 2
            p = Producto.query.get(2)
            if not p:
                print("ERROR: Producto 2 no encontrado")
                return
                
            print(f"Producto encontrado: {p.nombre}")
            
            # 2. Probar to_dict
            print("Probando to_dict()...")
            try:
                d = p.to_dict()
                print("✓ to_dict exitoso")
            except Exception as e:
                print(f"❌ FALLO EN to_dict: {str(e)}")
                import traceback
                traceback.print_exc()
                return

            # 3. Probar actualización de campos básicos
            print("Probando actualización de campos...")
            p.nombre = p.nombre # No cambio nada realmente, solo commit
            db.session.commit()
            print("✓ Commit básico exitoso")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ FALLO EN OPERACIÓN: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_product_update()
