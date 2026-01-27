from app import app
from models import db, Producto

with app.app_context():
    print("--- DIAGNOSTICO DE PRECIOS ---")
    
    # Buscar productos con precio alto (cerca de 150k) o el de la captura "Remera 3 x 10"
    # Buscamos por nombre aproximado
    products = Producto.query.filter(Producto.nombre.ilike('%Remera%')).all()
    
    print(f"Productos encontrados: {len(products)}")
    
    with open('diag_products_output.txt', 'w', encoding='utf-8') as f:
        for p in products:
            f.write(f"ID: {p.id}\n")
            f.write(f"  Nombre: {p.nombre}\n")
            f.write(f"  Precio Base: {p.precio_base}\n")
            f.write(f"  Precio Descuento: {p.precio_descuento}\n")
            f.write(f"  Precio Actual: {p.get_precio_actual()}\n")
            f.write("-" * 20 + "\n")
            
        # Check specific product from screenshot "Remera 3 x 10"
        specific = Producto.query.filter(Producto.nombre.ilike('%3 x 10%')).all()
        f.write("\n--- BÚSQUEDA ESPECÍFICA '3 x 10' ---\n")
        for p in specific:
             f.write(f"ID: {p.id} - Nombre: {p.nombre} - Base: {p.precio_base}\n")
        
    # Check general stats
    total_prods = Producto.query.count()
    print(f"Total Productos en DB: {total_prods}")
