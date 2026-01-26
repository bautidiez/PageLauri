from app import app
from models import db, Categoria

with app.app_context():
    def dump_cat(cat, level=0):
        print("  " * level + f"- {cat.nombre} (ID: {cat.id}, Slug: {cat.slug}, Activa: {cat.activa}, Orden: {cat.orden})")
        subs = Categoria.query.filter_by(categoria_padre_id=cat.id).order_by(Categoria.orden).all()
        for sub in subs:
            dump_cat(sub, level + 1)

    raices = Categoria.query.filter_by(categoria_padre_id=None).order_by(Categoria.orden).all()
    print(f"Total categorias raices: {len(raices)}")
    for r in raices:
        dump_cat(r)
