
from app import app
from models import Cliente, Pedido
from sqlalchemy import text

with app.app_context():
    print("--- DEBUG DUMP ---")
    
    print("\n1. SEARCHING 'diez' in Clients:")
    clients = Cliente.query.filter(Cliente.email.ilike('%diez%')).all()
    for c in clients:
        print(f"ID: {c.id} | Name: {c.nombre} | Email: '{c.email}' | Phone: '{c.telefono}'")
        
    print("\n2. SEARCHING 'diez' in Orders:")
    orders = Pedido.query.filter(Pedido.cliente_email.ilike('%diez%')).all()
    for o in orders:
        print(f"Order: {o.numero_pedido} | Email: '{o.cliente_email}' | Phone: '{o.cliente_telefono}' | Created: {o.created_at}")

    print("\n3. SEARCHING Phone '4171716' in Orders:")
    orders_phone = Pedido.query.filter(Pedido.cliente_telefono.ilike('%4171716%')).all()
    for o in orders_phone:
        print(f"Order: {o.numero_pedido} | Email: '{o.cliente_email}' | Phone: '{o.cliente_telefono}'")
