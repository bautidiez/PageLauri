
from app import app, db
from models import Cliente, Pedido, MetodoPago
from flask_jwt_extended import create_access_token

def test_search():
    with app.app_context():
        print("--- SETUP ---")
        # Ensure clean state for test
        email_base = "usuario.prueba@gmail.com"
        
        # 1. Create Client with Mixed Case
        client_email = "Usuario.Prueba@gmail.com"
        cliente = Cliente.query.filter_by(email=client_email).first()
        if not cliente:
            print(f"Creating client: {client_email}")
            cliente = Cliente(nombre="Test User", email=client_email, password_hash="hash")
            db.session.add(cliente)
            db.session.commit()
        else:
            print(f"Client exists: {cliente.email}")

        client_id = cliente.id
        
        # 2. Create Orders with variations
        variations = [
            "usuario.prueba@gmail.com",   # Exact match normalized
            "Usuario.Prueba@gmail.com",   # Exact match raw
            " usuario.prueba@gmail.com ", # Spaces
            "Usuario.Prueba@gmail.com ",  # Mixed + Space
        ]
        
        metodo = MetodoPago.query.first()
        if not metodo:
            metodo = MetodoPago(nombre="Efectivo", activo=True)
            db.session.add(metodo)
            db.session.commit()

        for i, var_email in enumerate(variations):
            # Check if order exists
            import random
            order_num = f"TEST{random.randint(10000, 99999)}"
            existing = Pedido.query.filter_by(numero_pedido=order_num).first()
            if not existing:
                print(f"Creating order with email: '{var_email}'")
                p = Pedido(
                    numero_pedido=order_num,
                    cliente_nombre="Test",
                    cliente_email=var_email, # Saving RAW
                    cliente_direccion="Calle Falsa 123",
                    cliente_codigo_postal="1234",
                    cliente_localidad="CABA",
                    cliente_provincia="BA",
                    metodo_pago_id=metodo.id,
                    subtotal=100,
                    total=100
                )
                db.session.add(p)
        db.session.commit()

        # 3. Simulate get_my_orders
        print("\n--- TESTING SEARCH ---")
        
        # Logic from clients.py (SIMULATION)
        pedidos_map = {}
        search_email = cliente.email.strip().lower()

        # 1. Email Search
        pedidos_email_exact = Pedido.query.filter(Pedido.cliente_email == search_email).all()
        for p in pedidos_email_exact: pedidos_map[p.id] = p
        
        pedidos_email_like = Pedido.query.filter(Pedido.cliente_email.ilike(f"%{search_email}%")).all()
        for p in pedidos_email_like: pedidos_map[p.id] = p

        # 2. Phone Search
        cliente.telefono = "11-1234-5678" # Set test phone
        clean_phone = "".join(filter(str.isdigit, str(cliente.telefono)))
        print(f"Testing phone: {clean_phone}")
        
        # Create "Lost" Order (Different email, but matching phone)
        import random
        lost_id = f"LOST{random.randint(1000, 9999)}"
        lost_order = Pedido(
            numero_pedido=lost_id,
            cliente_nombre="Lost User",
            cliente_email="typo@email.com", 
            cliente_telefono="+54 9 11 1234 5678", # Contains 1112345678
            cliente_direccion="Nowhere",
            cliente_codigo_postal="0000",
            cliente_localidad="Void",
            cliente_provincia="V",
            metodo_pago_id=1,
            subtotal=99,
            total=99
        )
        db.session.add(lost_order)
        db.session.commit()
        
        if len(clean_phone) >= 7:
            pedidos_fono = Pedido.query.filter(Pedido.cliente_telefono.ilike(f"%{clean_phone}%")).all()
            for p in pedidos_fono:
                pedidos_map[p.id] = p
                print(f"Found by Phone: {p.numero_pedido} ({p.cliente_email})")
                
        pedidos_finales = list(pedidos_map.values())
        print(f"Total Found: {len(pedidos_finales)}")

if __name__ == "__main__":
    test_search()
