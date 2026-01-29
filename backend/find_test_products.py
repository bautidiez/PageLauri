from app import app
from models import Producto

with app.app_context():
    short = Producto.query.filter_by(categoria_id=8, activo=True).first()
    remera = Producto.query.filter_by(categoria_id=13, activo=True).first()
    
    if short:
        print(f"SHORT_ID={short.id}")
        print(f"SHORT_PRECIO={short.precio_base}")
    if remera:
        print(f"REMERA_ID={remera.id}")
        print(f"REMERA_PRECIO={remera.precio_base}")
