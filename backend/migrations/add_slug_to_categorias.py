import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app, db
from models import Categoria
from sqlalchemy import text
import re
import unicodedata

def slugify(value):
    """
    Normalizes string, converts to lowercase, removes non-alpha characters,
    and converts spaces to hyphens.
    """
    value = str(value)
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
    value = re.sub(r'[^\w\s-]', '', value.lower())
    return re.sub(r'[-\s]+', '-', value).strip('-')

def run_migration():
    with app.app_context():
        print("Checking if 'slug' column exists...")
        engine = db.engine
        inspector = db.inspect(engine)
        columns = [col['name'] for col in inspector.get_columns('categorias')]
        
        if 'slug' not in columns:
            print("Adding 'slug' column to 'categorias' table...")
            with engine.connect() as conn:
                conn.execute(text("ALTER TABLE categorias ADD COLUMN slug VARCHAR(100)"))
                # SQLite doesn't support adding unique constraint in ALTER TABLE easily in one go, 
                # but we can try index creation or just trust our update logic first.
                # For PostgreSQL (which user seems to be using based on previous context or just SQL), syntax is correct.
                # Just in case it's SQLite, separate index creation.
                try:
                    conn.execute(text("CREATE UNIQUE INDEX idx_categoria_slug ON categorias (slug)"))
                except Exception as e:
                    print(f"Index creation warning (might already exist or not supported): {e}")
                conn.commit()
            print("Column added.")
        else:
            print("'slug' column already exists.")

        print("Populating slugs for existing categories...")
        categorias = Categoria.query.all()
        count = 0
        for cat in categorias:
            if not cat.slug:
                base_slug = slugify(cat.nombre)
                slug = base_slug
                counter = 1
                # Ensure uniqueness
                while Categoria.query.filter_by(slug=slug).first():
                    slug = f"{base_slug}-{counter}"
                    counter += 1
                
                cat.slug = slug
                count += 1
                print(f"Updated: {cat.nombre} -> {cat.slug}")
        
        if count > 0:
            db.session.commit()
            print(f"Successfully updated {count} categories.")
        else:
            print("No categories needed updating.")

if __name__ == "__main__":
    run_migration()
