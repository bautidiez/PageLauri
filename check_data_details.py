import requests
import json

BACKEND_URL = "https://elvestuario-backend.onrender.com"

print("--- Product Data Diagnostic ---")
try:
    # 1. Check all products (including inactive) via a more direct way if possible, or just look at the public list
    r = requests.get(f"{BACKEND_URL}/api/productos")
    if r.status_code == 200:
        productos = r.json()
        print(f"Total products returned by /api/productos: {len(productos)}")
        if len(productos) > 0:
            first = productos[0]
            print(f"Sample product: {first.get('nombre')} (ID: {first.get('id')})")
            print(f"Status: activo={first.get('activo')}, tiene_stock={first.get('tiene_stock')}")
            
            # Count active vs inactive in the response
            active_count = sum(1 for p in productos if p.get('activo'))
            print(f"Active in list: {active_count}")
            
            # Check for categories
            rcat = requests.get(f"{BACKEND_URL}/api/categorias")
            if rcat.status_code == 200:
                categorias = rcat.json()
                print(f"Total categories: {len(categorias)}")
            else:
                print(f"Error fetching categories: {rcat.status_code}")
        else:
            print("WARNING: /api/productos returned an EMPTY list.")
    else:
        print(f"Error: {r.status_code} - {r.text}")
except Exception as e:
    print(f"Exception: {e}")
