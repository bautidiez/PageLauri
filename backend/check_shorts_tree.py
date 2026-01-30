from app import app
from models import Categoria

with app.app_context():
    shorts = Categoria.query.get(8)
    if not shorts:
        print("Categoria Shorts (8) no encontrada")
        exit()

    print(f"Raiz: {shorts.id} - {shorts.nombre}")
    
    # Nivel 1
    children = Categoria.query.filter_by(categoria_padre_id=8).all()
    all_shorts_ids = [8]
    
    for child in children:
        print(f"  - Hijo: {child.id} - {child.nombre}")
        all_shorts_ids.append(child.id)
        
        # Nivel 2 (si existe)
        grandchecker = Categoria.query.filter_by(categoria_padre_id=child.id).all()
        for grand in grandchecker:
             print(f"    - Nieto: {grand.id} - {grand.nombre}")
             all_shorts_ids.append(grand.id)

    print(f"\nTodos los IDs de Shorts: {all_shorts_ids}")
