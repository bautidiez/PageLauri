"""
Minimal test - can we load productos?
"""
import sys
sys.path.insert(0, '.')

try:
    print("1. Importing app...")
    from app import app, db
    
    print("2. Importing models...")
    from models import Producto
    
    with app.app_context():
        print("3. Querying first product...")
        producto = Producto.query.first()
        
        if not producto:
            print("✗ No products found in database")
            sys.exit(1)
        
        print(f"✓ Got product: {producto.nombre}")
        
        print("4. Converting to dict (WITHOUT promociones)...")
        # Temporarily bypass promocion loading
        old_get = producto.get_promociones_activas
        producto.get_promociones_activas = lambda: []
        
        data = producto.to_dict()
        print(f"✓ to_dict() works! Keys: {list(data.keys())[:10]}...")
        
        print("\n5. Calling get_promociones_activas()...")  
        producto.get_promociones_activas = old_get
        try:
            promos = producto.get_promociones_activas()
            print(f"✓ get_promociones_activas() works! Got {len(promos)} promos")
        except Exception as e:
            print(f"✗ ERROR in get_promociones_activas(): {e}")
            import traceback
            traceback.print_exc()
            
except Exception as e:
    print(f"✗ FATAL ERROR:  {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
