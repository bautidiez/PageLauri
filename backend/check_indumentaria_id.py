from app import app
from models import db, Categoria
import sys

sys.stdout.reconfigure(encoding='utf-8')

with app.app_context():
    indu = Categoria.query.filter_by(slug='indumentaria').first()
    if indu:
        print(f"INDUMENTARIA ID: {indu.id}")
    else:
        print("INDUMENTARIA NOT FOUND")
        
    f79 = Categoria.query.get(79)
    if f79:
        print(f"ID 79 IS: {f79.nombre}")
    else:
        print("ID 79 DOES NOT EXIST")
