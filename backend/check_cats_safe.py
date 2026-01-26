from app import app
from models import db, Categoria
import sys

# Force encoding
sys.stdout.reconfigure(encoding='utf-8')

with app.app_context():
    cats = Categoria.query.all()
    print(f"Total categories: {len(cats)}")
    for c in cats:
        try:
            print(f"ID: {c.id} | Slug: '{c.slug}' | Name: '{c.nombre}' | Parent: {c.categoria_padre_id}")
        except Exception:
            print(f"ID: {c.id} | (Name encoding error)")
