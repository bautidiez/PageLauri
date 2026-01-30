from app import app
from models import Producto, Talle

with app.app_context():
    # Get a product with stock
    p = Producto.query.filter(Producto.stock_talles.any()).first()
    if p:
        print(f"Producto: {p.nombre} (ID: {p.id})")
        print("Stock Talles (raw dict):")
        # Simulate to_dict() logic if possible, or just print relationships
        # Assuming to_dict is used in API
        print(p.to_dict()['stock_talles'])
    else:
        print("No product with stock found?")

    # List Talles
    print("\nTalles:")
    talles = Talle.query.all()
    for t in talles:
        print(f"ID: {t.id} Name: {t.nombre}")
