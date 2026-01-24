
import os
import sys
sys.path.append(os.getcwd())
from app import app
from models import Categoria

def debug_categories():
    with app.app_context():
        cats = Categoria.query.all()
        with open('cats_debug.txt', 'w', encoding='utf-8') as f:
            for c in cats:
                line = f"{c.id} | {c.nombre} | {c.categoria_padre_id} | {c.get_nivel()} | Activa: {c.activa}\n"
                f.write(line)

if __name__ == '__main__':
    debug_categories()
