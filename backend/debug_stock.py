from app import app, db
from models import Producto, StockTalle

with app.app_context():
    p = Producto.query.get(66)
    if p:
        print(f"Producto: {p.nombre} (ID: {p.id})")
        print(f"  tiene_stock() [>= 6]: {p.tiene_stock()}")
        print(f"  tiene_stock_bajo() [1-5]: {p.tiene_stock_bajo()}")
        sts = StockTalle.query.filter_by(producto_id=66).all()
        print(f"  Total stock entries: {len(sts)}")
        for st in sts:
            print(f"    - ID {st.id}, Color {st.color_id}, Talle {st.talle_id}, Cantidad {st.cantidad}")
    else:
        print("Producto con ID 66 no encontrado")
