from app import app
from models import db, MetodoPago

with app.app_context():
    metodos = MetodoPago.query.all()
    print("-" * 30)
    for m in metodos:
        print(f"ID: {m.id} | Nombre: '{m.nombre}' | Activo: {m.activo}")
    print("-" * 30)
