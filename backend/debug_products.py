from app import app, db
from models import Producto, Categoria

def check_products():
    with app.app_context():
        total = Producto.query.count()
        activos = Producto.query.filter_by(activo=True).count()
        destacados = Producto.query.filter_by(destacado=True).count()
        categorias = Categoria.query.count()
        
        print(f"--- DEBUG REPORT ---")
        print(f"Total Categorias: {categorias}")
        print(f"Total Productos: {total}")
        print(f"Active Products: {activos}")
        print(f"Destacados: {destacados}")
        
        if activos == 0 and total > 0:
            print("WARNING: You have products but none are active!")
        
        if total > 0:
            p = Producto.query.first()
            print(f"Sample Product: {p.nombre} (Activo: {p.activo}, Categoria: {p.categoria.nombre if p.categoria else 'None'})")
            print(f"Imagenes: {len(p.imagenes)} associated")
            if p.imagenes:
                print(f"Sample Image URL: {p.imagenes[0].url}")
                
        # Simulate API Request
        print("\n--- API SIMULATION (/api/productos) ---")
        app.testing = True
        client = app.test_client()
        try:
            response = client.get('/api/productos')
            print(f"Status Code: {response.status_code}")
            if response.status_code == 200:
                data = response.get_json()
                print(f"API Returned Total: {data.get('total')}")
                print(f"API Returned Items Count: {len(data.get('items', []))}")
            else:
                print(f"API Error: {response.data}")
        except Exception as e:
            import traceback
            print("EXCEPTION CAUGHT:")
            traceback.print_exc()

if __name__ == "__main__":
    import sys
    # Redirect stdout and stderr to file
    with open('debug_output.txt', 'w', encoding='utf-8') as f:
        sys.stdout = f
        sys.stderr = f
        check_products()
        print("Debug report written to debug_output.txt")
