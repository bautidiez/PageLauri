
from app import app
from models import Pedido, Cliente

with app.app_context():
    email = "baulediez@gmail.com"
    print(f"--- Debugging for {email} ---")
    
    # Check Client
    cliente = Cliente.query.filter_by(email=email).first()
    if cliente:
        print(f"Cliente Found: ID={cliente.id}, Email={cliente.email}, Name={cliente.nombre}")
    else:
        print("Cliente NOT found.")

    # Check Orders exact match
    orders_exact = Pedido.query.filter(Pedido.cliente_email == email).all()
    print(f"Orders exact match: {len(orders_exact)}")
    for o in orders_exact:
        print(f" - Order {o.numero_pedido}: Email='{o.cliente_email}', State={o.estado}")

    # Check Orders partial match
    orders_like = Pedido.query.filter(Pedido.cliente_email.ilike(f"%{email}%")).all()
    print(f"Orders like match: {len(orders_like)}")
    
    # Check all recent orders to see if there's a typo
    print("--- Recent 5 orders ---")
    recent = Pedido.query.order_by(Pedido.created_at.desc()).limit(5).all()
    for o in recent:
        print(f" - {o.numero_pedido}: {o.cliente_email} ({o.cliente_nombre})")
