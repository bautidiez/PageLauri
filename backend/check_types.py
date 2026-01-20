
from app import app, db
from models import TipoPromocion

with app.app_context():
    tipos = TipoPromocion.query.all()
    for t in tipos:
        print(f"ID: {t.id}, Nombre: {t.nombre}, Descripcion: {t.descripcion}")
