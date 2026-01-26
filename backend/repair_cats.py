from app import app
from models import db, Categoria

with app.app_context():
    # 1. Crear categorías raíz faltantes si no existen
    root_defs = [
        {'nombre': 'Indumentaria', 'slug': 'indumentaria', 'orden': 1},
        {'nombre': 'Accesorios', 'slug': 'accesorios', 'orden': 2},
    ]

    roots = {}
    for rdef in root_defs:
        cat = Categoria.query.filter_by(slug=rdef['slug']).first()
        if not cat:
            print(f"Creating root category: {rdef['nombre']}")
            cat = Categoria(
                nombre=rdef['nombre'],
                slug=rdef['slug'],
                orden=rdef['orden'],
                activa=True
            )
            db.session.add(cat)
            db.session.commit()
        roots[rdef['slug']] = cat

    # 2. Mapear subcategorías huérfanas
    # Asumimos que la mayoría van a 'Indumentaria' excepto algunas obvias
    orphans = Categoria.query.filter(Categoria.categoria_padre_id.is_(None), ~Categoria.slug.in_(['indumentaria', 'accesorios'])).all()
    
    print(f"Found {len(orphans)} orphan root categories. Re-linking...")
    
    for cat in orphans:
        # Lógica simple de asignación
        new_parent = roots['indumentaria'] # Default
        
        name_lower = cat.nombre.lower()
        if 'gorra' in name_lower or 'medias' in name_lower or 'mochila' in name_lower or 'piluso' in name_lower:
            new_parent = roots['accesorios']
        
        print(f"Linking '{cat.nombre}' -> '{new_parent.nombre}'")
        cat.categoria_padre_id = new_parent.id
        
    db.session.commit()
    print("Categories repaired successfully.")
