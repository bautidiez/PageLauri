from app import app, db
from models import MetodoPago

with app.app_context():
    methods = MetodoPago.query.all()
    print("Payment Methods:")
    for m in methods:
        print(f"ID: {m.id}, Nombre: {m.nombre}")
