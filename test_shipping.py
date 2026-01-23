import sys
import os

# Añadir el directorio actual al path para poder importar services
sys.path.append(os.path.abspath('backend'))

try:
    from backend.services.shipping_service import ShippingService
    print("Testing ShippingService...")
    rates = ShippingService.calculate_cost("1425")
    print(f"Rates found: {len(rates)}")
    for r in rates:
        print(f" - {r['nombre']}: ${r['costo']}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
