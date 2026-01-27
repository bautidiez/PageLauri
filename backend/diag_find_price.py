from app import app
from models import db, Producto

with app.app_context():
    print("--- BUSQUEDA POR PRECIO ---")
    
    # Buscar productos con precio base > 100000
    products = Producto.query.filter(Producto.precio_base > 100000).all()
    
    print(f"Productos > 100k: {len(products)}")
    for p in products:
        print(f"ID: {p.id}")
        print(f"  Nombre: {p.nombre}")
        print(f"  Precio Base: {p.precio_base}")
        print("-" * 20)
        
    # Buscar con oferta > 100k
    products_off = Producto.query.filter(Producto.precio_descuento > 100000).all()
    print(f"Productos Oferta > 100k: {len(products_off)}")
    for p in products_off:
        print(f"ID: {p.id} - {p.nombre} - ${p.precio_descuento}")
