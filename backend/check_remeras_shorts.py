from app import app
from models import db, Categoria
import sys

sys.stdout.reconfigure(encoding='utf-8')

with app.app_context():
    # Check Remeras
    remeras = Categoria.query.filter(Categoria.nombre.ilike('Remera%')).all()
    print(f"--- REMERAS ({len(remeras)}) ---")
    for c in remeras:
        print(f"ID:{c.id} Name:'{c.nombre}' Slug:'{c.slug}' Parent:{c.categoria_padre_id}")

    # Check Shorts
    shorts = Categoria.query.filter(Categoria.nombre.ilike('Short%')).all()
    print(f"--- SHORTS ({len(shorts)}) ---")
    for c in shorts:
        print(f"ID:{c.id} Name:'{c.nombre}' Slug:'{c.slug}' Parent:{c.categoria_padre_id}")

    # Check Roots
    roots = Categoria.query.filter_by(categoria_padre_id=None).all()
    print(f"--- ROOTS ({len(roots)}) ---")
    for c in roots:
        print(f"ID:{c.id} Name:'{c.nombre}' Slug:'{c.slug}'")
