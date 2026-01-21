import requests

BACKEND_URL = "https://elvestuario-backend.onrender.com"

print("Scanning for products by ID (1-100)...")
found = []
for i in range(1, 101):
    try:
        r = requests.get(f"{BACKEND_URL}/api/productos/{i}")
        if r.status_code == 200:
            p = r.json()
            found.append(f"ID {i}: {p.get('nombre')}")
    except:
        pass

if found:
    print("Found products:")
    for f in found:
        print(f" - {f}")
else:
    print("No products found by ID scan.")

# Also check categories scan
print("\nScanning for categories by ID (1-50)...")
cats_found = []
for i in range(1, 51):
    try:
        # Note: /api/categorias takes ?categoria_padre_id, so let's try a direct detail if exists.
        # But looking at store_public.py, there is NO /api/categorias/<id> public route.
        # So we just rely on /api/categorias.
        pass
    except:
        pass

r_cats = requests.get(f"{BACKEND_URL}/api/categorias")
if r_cats.status_code == 200:
    cats = r_cats.json()
    print(f"Total categories from list: {len(cats)}")
