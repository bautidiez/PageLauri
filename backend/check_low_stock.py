from app import app, db
from models import StockTalle, Producto

with app.app_context():
    sts = StockTalle.query.filter(StockTalle.cantidad > 0, StockTalle.cantidad <= 5).all()
    print(f"Total entries with 1-5 stock: {len(sts)}")
    
    unique_product_ids = {st.producto_id for st in sts}
    print(f"Unique product IDs: {unique_product_ids}")
    
    for pid in unique_product_ids:
        p = Producto.query.get(pid)
        print(f"Product {p.nombre} (ID: {pid}) has low stock")
