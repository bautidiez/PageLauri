from app import app
from models import db, MetodoPago

METHODS = [
    {'nombre': 'efectivo', 'descripcion': 'Efectivo / Rapipago / Pago Fácil'},
    {'nombre': 'efectivo_local', 'descripcion': 'Efectivo en el Local (15% OFF)'},
    {'nombre': 'mercadopago', 'descripcion': 'Mercado Pago (Tarjeta)'}
]

with app.app_context():
    for m in METHODS:
        existing = MetodoPago.query.filter_by(nombre=m['nombre']).first()
        if not existing:
            new_method = MetodoPago(nombre=m['nombre'], descripcion=m['descripcion'], activo=True)
            db.session.add(new_method)
            print(f"Adding {m['nombre']}...")
        else:
            print(f"{m['nombre']} already exists.")
    
    db.session.commit()
    print("Payment methods updated.")
