from app import app
from models import db, Categoria

with app.app_context():
    cats = Categoria.query.all()
    print(f"Total: {len(cats)}")
    for c in cats:
        print(f"ID: {c.id} | Slug: '{c.slug}' | Nombre: '{c.nombre}'")
