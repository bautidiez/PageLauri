from app import app, db
from models import StockTalle, Producto

with app.app_context():
    # List top 10 stock entries
    stocks = StockTalle.query.limit(20).all()
    print(f"Found {len(stocks)} stock entries.")
    for s in stocks:
        prod = Producto.query.get(s.producto_id)
        if prod and prod.activo:
             print(f"Prod: {prod.id} ({prod.nombre}) Cat:{prod.categoria_id} Talle:{s.talle_id} Qty:{s.cantidad}")
