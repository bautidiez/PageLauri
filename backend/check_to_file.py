from app import app
from models import db, Categoria
import sys

with app.app_context():
    with open('summary.txt', 'w', encoding='utf-8') as f:
        # Check Remeras
        remeras = Categoria.query.filter(Categoria.nombre.ilike('Remera%')).all()
        f.write(f"REMERAS COUNT: {len(remeras)}\n")
        for c in remeras:
            f.write(f"ID:{c.id} Name:{c.nombre} Slug:{c.slug} Parent:{c.categoria_padre_id}\n")

        # Check Shorts
        shorts = Categoria.query.filter(Categoria.nombre.ilike('Short%')).all()
        f.write(f"SHORTS COUNT: {len(shorts)}\n")
        for c in shorts:
            f.write(f"ID:{c.id} Name:{c.nombre} Slug:{c.slug} Parent:{c.categoria_padre_id}\n")

        # Check Roots
        roots = Categoria.query.filter_by(categoria_padre_id=None).all()
        f.write(f"ROOTS COUNT: {len(roots)}\n")
        for c in roots:
            f.write(f"ID:{c.id} Name:{c.nombre} Slug:{c.slug}\n")
