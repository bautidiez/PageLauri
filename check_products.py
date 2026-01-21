import requests

BACKEND_URL = "https://elvestuario-backend.onrender.com"

print("Checking product count...")
try:
    r = requests.get(f"{BACKEND_URL}/api/productos")
    if r.status_code == 200:
        productos = r.json()
        print(f"Total products found: {len(productos)}")
    else:
        print(f"Error: {r.status_code} - {r.text}")
except Exception as e:
    print(f"Exception: {e}")
