from app import app
from models import Producto, Categoria

with app.app_context():
    # 1. Try ID 51 via filter
    p51 = Producto.query.filter_by(id=51).first()
    if p51:
        print(f"FOUND ID 51: {p51.nombre} (Cat: {p51.categoria_id})")
        # Check Ancestry
        c = Categoria.query.get(p51.categoria_id)
        while c:
            print(f" -> {c.nombre} ({c.id})")
            c = c.categoria_padre
    else:
        print("!!! ID 51 NOT FOUND via filter_by(id=51)")

    # 2. Search name "Tottenham"
    ps = Producto.query.filter(Producto.nombre.ilike('%Tottenham%')).all()
    print(f"Found {len(ps)} products with 'Tottenham':")
    for p in ps:
        print(f" - {p.nombre} (ID: {p.id}) Cat: {p.categoria_id}")



    # 2. Check Category 8
    c8 = Categoria.query.get(8)
    if c8:
        print(f"Category 8: {c8.nombre}")
    else:
        print("!!! Category 8 NOT FOUND")
