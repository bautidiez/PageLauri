from app import app, db
from models import Categoria

with app.app_context():
    with open("cats_output_simple.txt", "w", encoding="utf-8") as f:
        cats = Categoria.query.all()
        for c in cats:
            f.write(f"ID: {c.id}, Nombre: '{c.nombre}'\n")
