"""Script para probar el endpoint de stock"""
import requests

# Primero obtener token de admin
login_response = requests.post('http://localhost:5000/api/auth/login', json={
    'username': 'admin',
    'password': 'admin123'
})

if login_response.status_code == 200:
    token = login_response.json()['access_token']
    print(f"✅ Login exitoso, token obtenido")
    
    # Buscar Remera 1
    headers = {'Authorization': f'Bearer {token}'}
    search_response = requests.get('http://localhost:5000/api/admin/products/search?q=Remera', headers=headers)
    
    if search_response.status_code == 200:
        productos = search_response.json()
        print(f"\n📦 Productos encontrados: {len(productos)}")
        
        if productos:
            remera = productos[0]
            producto_id = remera['id']
            print(f"\nUsando: {remera['nombre']} (ID: {producto_id})")
            
            # Obtener stock para este producto
            stock_response = requests.get(
                f'http://localhost:5000/api/admin/stock?producto_id={producto_id}',
                headers=headers
            )
            
            print(f"\n🔍 Status de respuesta: {stock_response.status_code}")
            
            if stock_response.status_code == 200:
                stock_data = stock_response.json()
                print(f"\n📊 Respuesta del backend:")
                print(f"  - items: {len(stock_data.get('items', []))} registros")
                print(f"  - total: {stock_data.get('total', 0)}")
                
                if stock_data.get('items'):
                    print("\nDetalle del stock:")
                    for item in stock_data['items']:
                        print(f"  - Talle: {item.get('talle_nombre')} (ID: {item.get('talle_id')}) - Cantidad: {item.get('cantidad')}")
                else:
                    print("\n⚠️ El backend devolvió una lista vacía")
                    print(f"\nRespuesta completa: {stock_data}")
            else:
                print(f"❌ Error en stock endpoint: {stock_response.text}")
        else:
            print("❌ No se encontraron productos")
    else:
        print(f"❌ Error en search: {search_response.text}")
else:
    print(f"❌ Error en login: {login_response.text}")
