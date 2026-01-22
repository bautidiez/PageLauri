import os
import sys

# Add the parent directory to the path so we can import the app and models
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from app import app
    from models import db, Talle, StockTalle
    
    with app.app_context():
        # Find the XS size
        talle_xs = Talle.query.filter_by(nombre='XS').first()
        
        if talle_xs:
            print(f"Encontrado talle XS (ID: {talle_xs.id})")
            
            # Delete associated stock
            deleted_stock = StockTalle.query.filter_by(talle_id=talle_xs.id).delete()
            print(f"Eliminados {deleted_stock} registros de stock asociados a XS")
            
            # Delete the size
            db.session.delete(talle_xs)
            db.session.commit()
            print("Talle XS eliminado con éxito.")
        else:
            print("No se encontró el talle XS en la base de datos.")
            
except Exception as e:
    print(f"Error durante la migración: {str(e)}")
