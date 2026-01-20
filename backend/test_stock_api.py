"""
Script para debuggear el problema de stock en ventas externas
"""
import sys
sys.path.insert(0, '.')

from app import app
from models import db, Producto, StockTalle, Talle

with app.app_context():
    # Buscar productos con "Remera" en el nombre
    productos = Producto.query.filter(Producto.nombre.like('%Remera%')).all()
    
    print("\n=== PRODUCTOS CON 'REMERA' ===")
    for p in productos:
        print(f"\nID: {p.id}")
        print(f"Nombre: {p.nombre}")
        print(f"Activo: {p.activo}")
        
        # Buscar el stock de este producto
        stocks = StockTalle.query.filter_by(producto_id=p.id).all()
        
        if stocks:
            print(f"Stock encontrado:")
            for s in stocks:
                talle = Talle.query.get(s.talle_id)
                print(f"  - Talle {talle.nombre} (ID: {s.talle_id}): {s.cantidad} unidades")
                # Verificar el to_dict()
                stock_dict = s.to_dict()
                print(f"    to_dict(): {stock_dict}")
        else:
            print("  ⚠️  SIN STOCK registrado")
    
    # Probar el query que hace el endpoint
    print("\n\n=== SIMULANDO EL QUERY DEL ENDPOINT ===")
    if productos:
        producto_id = productos[0].id
        print(f"Consultando stock para producto_id={producto_id}")
        
        query = StockTalle.query.join(Producto).join(Talle)
        query = query.filter(StockTalle.producto_id == producto_id)
        
        results = query.all()
        print(f"Resultados encontrados: {len(results)}")
        
        for s in results:
            result_dict = s.to_dict()
            print(f"  Stock: {result_dict}")
