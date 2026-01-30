from app import app
from models import Producto, Categoria

with app.app_context():
    # List similar
    ps = Producto.query.filter(Producto.nombre.ilike('%Tottenham%')).all()
    for p in ps:
        print(f"Encontrado: {p.nombre} (ID: {p.id}, CatID: {p.categoria_id})")
        c = Categoria.query.get(p.categoria_id)
        while c:
            print(f" -> Cat: {c.nombre} (ID: {c.id})")
            c = c.categoria_padre
        print("---")
