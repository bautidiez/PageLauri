from app import app
from models import db, Categoria

with app.app_context():
    cats = Categoria.query.filter(Categoria.nombre.in_(['Remeras', 'Shorts'])).all()
    print(f"Found {len(cats)} categories.")
    for c in cats:
        print(f"ID: {c.id}, Nombre: '{c.nombre}', Slug: '{c.slug}', Padre: {c.categoria_padre_id}")
