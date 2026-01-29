from app import app, db
from models import StockTalle, Producto

with app.app_context():
    # Find Short with stock
    stock_short = db.session.query(StockTalle).join(Producto).filter(Producto.categoria_id == 8, StockTalle.cantidad > 0).first()
    if stock_short:
        print(f"FOUND_SHORT: {stock_short.producto_id} Talle: {stock_short.talle_id} Qty: {stock_short.cantidad}")
    else:
        print("NO_SHORT_STOCK_FOUND")
