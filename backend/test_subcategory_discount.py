from app import app, db
from services.order_service import OrderService
from models import Producto, Categoria, Talle, StockTalle, MetodoPago

with app.app_context():
    # 1. Asegurar setup
    # Crear categoria Short (8) y SubShort (999) si no existen
    short_cat = Categoria.query.get(8)
    if not short_cat:
        print("Error: Categoria 8 no existe. abortando.")
        exit()
        
    sub_short = Categoria.query.filter_by(nombre="SubShort Test").first()
    if not sub_short:
        sub_short = Categoria(nombre="SubShort Test", categoria_padre_id=8, slug="sub-short-test")
        db.session.add(sub_short)
        db.session.commit()
    
    print(f"Subcategory ID: {sub_short.id}, Parent: {sub_short.categoria_padre_id}")

    # Crear producto en SubShort
    prod = Producto.query.filter_by(nombre="Short Test Subcat").first()
    if not prod:
        prod = Producto(
            nombre="Short Test Subcat", 
            categoria_id=sub_short.id, 
            precio_base=10000, 
            precio_descuento=None,
            activo=True
        )
        db.session.add(prod)
        db.session.commit()
    
    # Asegurar Talle
    talle = Talle.query.first()
    
    # Asegurar Stock
    stock = StockTalle.query.filter_by(producto_id=prod.id, talle_id=talle.id).first()
    if not stock:
        stock = StockTalle(producto_id=prod.id, talle_id=talle.id, cantidad=10)
        db.session.add(stock)
        db.session.commit()
    
    # Metodo Pago Transferencia
    pago = MetodoPago.query.filter(MetodoPago.nombre.ilike("%transferencia%")).first()
    if not pago:
        pago = MetodoPago(nombre="Transferencia", activo=True)
        db.session.add(pago)
        db.session.commit()

    # 2. Crear Pedido
    data = {
        'cliente_nombre': 'Test Recur',
        'cliente_email': 'test@test.com',
        'metodo_pago_id': pago.id,
        'items': [{
            'producto_id': prod.id,
            'talle_id': talle.id,
            'cantidad': 1
        }]
    }
    
    try:
        pedido = OrderService.create_order(data)
        print(f"Pedido Total: {pedido.total}")
        print(f"Pedido Subtotal: {pedido.subtotal}")
        print(f"Pedido Descuento: {pedido.descuento}")
        
        # Esperado: 10% de 10000 = 1000 descuento. Total 9000.
        # Si fuera 15% (error), seria 1500 descuento.
        if pedido.descuento == 1000.0:
            print("SUCCESS: Descuento es 10% (Short Subcategory)")
        elif pedido.descuento == 1500.0:
            print("FAIL: Descuento es 15% (Standard) - Recursive check failed")
        else:
            print(f"FAIL: Descuento inesperado {pedido.descuento}")
            
    except Exception as e:
        print(f"Error creando pedido: {e}")
