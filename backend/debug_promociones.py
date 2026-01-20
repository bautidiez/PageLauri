"""
Debug script to test promociones queries
"""
import sys
sys.path.insert(0, '.')

from app import app, db
from models import Producto, PromocionProducto
from sqlalchemy import text

with app.app_context():
    # First, check the table structure
    result = db.session.execute(text("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'promociones_productos' 
        ORDER BY ordinal_position
    """))
    
    print("=" * 60)
    print("COLUMNS IN promociones_productos:")
    print("=" * 60)
    for row in result:
        print(f"  {row[0]:<30} {row[1]}")
    
    print("\n" + "=" * 60)
    print("TRYING TO QUERY PromocionProducto model...")
    print("=" * 60)
    
    try:
        # Try to query without loading relationships
        count = db.session.query(PromocionProducto).count()
        print(f"✓ Query successful! Found {count} promociones")
        
        # Try to get one
        if count > 0:
            promo = db.session.query(PromocionProducto).first()
            print(f"✓ First promo ID: {promo.id}")
            print(f"✓ Has compra_minima attr: {hasattr(promo, 'compra_minima')}")
            if hasattr(promo, 'compra_minima'):
                print(f"✓ compra_minima value: {promo.compra_minima}")
    except Exception as e:
        print(f"✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("TRYING TO QUERY Producto with promociones...")
    print("=" * 60)
    
    try:
        producto = db.session.query(Producto).first()
        if producto:
            print(f"✓ Got producto: {producto.nombre}")
            print(f"✓ Calling get_promociones_activas()...")
            promos = producto.get_promociones_activas()
            print(f"✓ Success! Got {len(promos)} promociones")
    except Exception as e:
        print(f"✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
