from app import app
from models import db, MetodoPago

with app.app_context():
    metodos = MetodoPago.query.all()
    with open('payment_methods.txt', 'w', encoding='utf-8') as f:
        f.write("-" * 30 + "\n")
        for m in metodos:
            f.write(f"ID: {m.id} | Nombre: {m.nombre} | Activo: {m.activo}\n")
        f.write("-" * 30 + "\n")
