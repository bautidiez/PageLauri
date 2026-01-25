
from app import app
from models import Pedido

with app.app_context():
    print("--- ORDER COUNT DUMP ---")
    count = Pedido.query.count()
    print(f"Total Orders in DB: {count}")
    
    print("\n--- ALL ORDERS ---")
    orders = Pedido.query.all()
    for o in orders:
        print(f"#{o.numero_pedido} | {o.cliente_email}")
