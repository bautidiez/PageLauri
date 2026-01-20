"""
Test ofertas API endpoint
"""
import requests

try:
    r = requests.get('http://localhost:5000/api/productos', params={
        'ofertas': 'true',
        'page': 1,
        'page_size': 100
    })
    
    print(f'Status: {r.status_code}')
    
    if r.status_code == 200:
        data = r.json()
        print(f'Total productos en ofertas: {data.get("total")}')
        print(f'Items en esta página: {len(data.get("items", []))}')
        
        # Mostrar los primeros 5 productos
        for i, p in enumerate(data.get('items', [])[:5], 1):
            print(f'{i}. {p.get("nombre")} - Precio: ${p.get("precio_base")} / Descuento: ${p.get("precio_descuento")}')
    else:
        print(f'Error: {r.text[:200]}')
        
except Exception as e:
    print(f'Error: {e}')
