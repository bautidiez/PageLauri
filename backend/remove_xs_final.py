
import os
import sys

# Add current directory to path
sys.path.append(os.getcwd())

from app import app
from models import Talle, db

def remove_xs():
    with app.app_context():
        talles = Talle.query.filter_by(nombre='XS').all()
        if talles:
            count = len(talles)
            Talle.query.filter_by(nombre='XS').delete()
            db.session.commit()
            print(f'Completado: Se eliminaron {count} entradas de "XS" de la base de datos.')
        else:
            print('Información: No se encontró el talle "XS" en la base de datos.')

if __name__ == '__main__':
    remove_xs()
