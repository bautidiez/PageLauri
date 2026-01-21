import requests
import json

BACKEND_URL = "https://elvestuario-backend.onrender.com"

print("--- Product Data Diagnostic (Extended) ---")
try:
    # 1. Total absolute count (we can't do this directly easily if we don't have a specific endpoint, 
    # but we can try /api/admin/productos if we had a token. 
    # However, let's just check /api/productos without filters first)
    r = requests.get(f"{BACKEND_URL}/api/productos")
    if r.status_code == 200:
        res = r.json()
        items = res.get('items', [])
        total = res.get('total', 0)
        print(f"Total from API (pagination total): {total}")
        print(f"Items in current page: {len(items)}")
        
        if len(items) > 0:
            for p in items[:5]:
                print(f"- {p.get('nombre')} (ID: {p.get('id')}) | Activo: {p.get('activo')} | Stock: {p.get('tiene_stock')}")
        else:
            print("No items returned in the first page.")
            
    # 2. Check categories
    r = requests.get(f"{BACKEND_URL}/api/categorias")
    if r.status_code == 200:
        cats = r.json()
        print(f"Categories found: {len(cats)}")
        for c in cats:
            print(f"- {c.get('nombre')} (ID: {c.get('id')})")
    
except Exception as e:
    print(f"Exception: {e}")
