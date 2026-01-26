from app import app
from models import db, Categoria
import sys

# Force encoding
sys.stdout.reconfigure(encoding='utf-8')

with app.app_context():
    # REMERAS
    remeras = Categoria.query.filter(Categoria.nombre == 'Remeras').all()
    print(f"REMERAS EXACT MATCHES: {len(remeras)}")
    for c in remeras:
        print(f"  ID:{c.id} Slug:{c.slug} Active:{c.activa} Parent:{c.categoria_padre_id}")
        
    # SHORTS
    shorts = Categoria.query.filter(Categoria.nombre == 'Shorts').all()
    print(f"SHORTS EXACT MATCHES: {len(shorts)}")
    for c in shorts:
        print(f"  ID:{c.id} Slug:{c.slug} Active:{c.activa} Parent:{c.categoria_padre_id}")
