from app import app
from models import db, Categoria
import unidecode
import re

def slugify(text):
    text = unidecode.unidecode(text).lower()
    return re.sub(r'[^a-z0-9]+', '-', text).strip('-')

with app.app_context():
    cats = Categoria.query.all()
    count = 0
    for c in cats:
        if not c.slug:
            new_slug = slugify(c.nombre)
            print(f"Fixing ID {c.id}: '{c.nombre}' -> '{new_slug}'")
            c.slug = new_slug
            count += 1
            
    if count > 0:
        db.session.commit()
        print(f"Updated {count} slugs.")
    else:
        print("No missing slugs found.")
