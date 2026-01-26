from app import app
from models import db, Categoria
import unicodedata
import re

def slugify(text):
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('utf-8')
    text = re.sub(r'[^\w\s-]', '', text).strip().lower()
    return re.sub(r'[-\s]+', '-', text)

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
