from app import app, db
from models import TipoPromocion, PromocionProducto
from sqlalchemy import inspect, text

with app.app_context():
    print("--- SEQUENCES ---")
    try:
        res = db.session.execute(text("SELECT last_value, is_called FROM promociones_productos_id_seq")).fetchone()
        max_id = db.session.execute(text("SELECT MAX(id) FROM promociones_productos")).scalar() or 0
        print(f"Sequence status: {res}")
        print(f"Max ID in table: {max_id}")
        if res and res[0] < max_id:
            print("⚠️ ADVERTENCIA: La secuencia está por debajo del MAX ID!")
    except Exception as e:
        print(f"Error revisando secuencias: {e}")

    print("\n--- TABLAS ---")
    print(inspect(db.engine).get_table_names())

    print("\n--- TIPOS DE PROMOCION ---")
    tipos = TipoPromocion.query.all()
    for t in tipos:
        print(t.to_dict())

    print("\n--- CODIGOS DE PROMOCION ---")
    promos = PromocionProducto.query.all()
    for p in promos:
        print(f"ID: {p.id}, Codigo: '{p.codigo}', Es Cupon: {p.es_cupon}")

    print("\n--- SCHEMA PROMOCIONES_PRODUCTOS ---")
    inst = inspect(db.engine)
    columns = inst.get_columns("promociones_productos")
    for col in columns:
        print(f"Columna: {col['name']}, Tipo: {col['type']}, Nullable: {col['nullable']}")
