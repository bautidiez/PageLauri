from app import app
from models import db, Categoria

# app = create_app() # No factory in app.py

with app.app_context():
    print("--- DIAGNOSTICO DE CATEGORIAS ---")
    
    with open('diag_output.txt', 'w', encoding='utf-8') as f:
        all_cats = Categoria.query.all()
        # Verify if sorting works
        try:
            roots = Categoria.query.filter_by(categoria_padre_id=None).order_by(Categoria.orden).all()
            f.write("Sort by Orden: SUCCESS\n")
        except Exception as e:
             f.write(f"Sort by Orden: FAILED - {str(e)}\n")
             roots = Categoria.query.filter_by(categoria_padre_id=None).all()
        
        f.write(f"Total Categorias: {len(all_cats)}\n")
        f.write(f"Total Raiz (None): {len(roots)}\n")
        
        for c in roots:
            f.write(f"Raiz: ID={c.id} Name='{c.nombre}' Active={c.activa} SubsCount={len(c.subcategorias)}\n")
            for s in c.subcategorias:
                 f.write(f"   - Sub: ID={s.id} Name='{s.nombre}' Active={s.activa}\n")
            
        roots_zero = Categoria.query.filter(Categoria.categoria_padre_id == 0).all()
        f.write(f"Total Raiz (0): {len(roots_zero)}\n")
        
    if not roots and all_cats:
        print("\nWARNING: Hay categorias pero ninguna es raiz (padre=None).")
        print("Muestra de categorias:")
        for c in all_cats[:5]:
            print(f"ID: {c.id} - {c.nombre} - PadreID: {c.categoria_padre_id}")
