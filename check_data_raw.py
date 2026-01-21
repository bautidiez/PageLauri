import requests
import json

BACKEND_URL = "https://elvestuario-backend.onrender.com"

print("--- RAW DATA DUMP ---")
try:
    # 1. Total products (any status)
    r = requests.get(f"{BACKEND_URL}/api/productos?activos=false&page_size=100")
    if r.status_code == 200:
        data = r.json()
        print(f"Total Products (activos=false): {data.get('total')}")
        items = data.get('items', [])
        print(f"Items returned: {len(items)}")
        
        # 2. Check first product details
        if items:
            p = items[0]
            print(f"Product [0]: {p.get('nombre')} | Activo: {p.get('activo')} | Categoria ID: {p.get('categoria_id')}")
    
    # 3. All categories
    r = requests.get(f"{BACKEND_URL}/api/categorias?incluir_subcategorias=false")
    if r.status_code == 200:
        cats = r.json()
        print(f"Total Categories: {len(cats)}")
        if cats:
            print(f"Cat [0]: {cats[0].get('nombre')} (ID: {cats[0].get('id')})")
    
except Exception as e:
    print(f"Error: {e}")
