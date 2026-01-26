from app import app
from models import db, Categoria

with app.app_context():
    roots = Categoria.query.filter_by(categoria_padre_id=None).all()
    print(f"ROOTS: {len(roots)}")
    for r in roots:
        print(f"ROOT ID: {r.id}, Name: {r.nombre}, Slug: {r.slug}")
        
    all_cats = Categoria.query.all()
    print(f"ALL: {len(all_cats)}")
    for c in all_cats:
        if c.categoria_padre_id is not None:
            print(f"CHILD ID: {c.id}, Name: {c.nombre}, Parent: {c.categoria_padre_id}")
