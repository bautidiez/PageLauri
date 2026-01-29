from app import app, db
from models import Categoria

with app.app_context():
    cats = Categoria.query.all()
    for c in cats:
        print(f"ID: {c.id}, Nombre: '{c.nombre}'")
