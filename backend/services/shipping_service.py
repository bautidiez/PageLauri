from .shipping_providers import AndreaniProvider, CorreoArgentinoProvider, TiendaNubeProvider
import logging

logger = logging.getLogger(__name__)

class ShippingService:
    @staticmethod
    def calculate_cost(zip_code, items=None):
        """
        Lógica completa de cotización desde Río Cuarto (CP 5800).
        """
        try:
            zip_code_val = int(zip_code)
        except (ValueError, TypeError):
            logger.error(f"ZIP code inválido: {zip_code}")
            return []

        # 1. Calcular peso y dimensiones agregadas
        total_weight = 0
        max_length = 0
        max_width = 0
        total_height = 0
        
        if not items:
            # Fallback a un bulto standard si no hay items definidos
            total_weight = 0.5
            dimensions = {"length": 30, "width": 20, "height": 5}
        else:
            for item in items:
                nombre = item.get('producto', {}).get('nombre', '').lower()
                cantidad = item.get('cantidad', 1)
                
                # Criterio según requerimiento
                if 'remera' in nombre:
                    w = 0.30
                    l, wd, h = 30, 20, 2 # cm
                elif 'short' in nombre:
                    w = 0.20
                    l, wd, h = 25, 15, 2
                else:
                    w = 0.25
                    l, wd, h = 25, 20, 2
                
                total_weight += (w * cantidad)
                max_length = max(max_length, l)
                max_width = max(max_width, wd)
                total_height += (h * cantidad)
            
            # Margen mínimo de empaque
            total_height = max(total_height, 2)
            dimensions = {
                "length": max_length,
                "width": max_width,
                "height": total_height
            }

        results = []
        
        # 2. Consultar proveedores
        providers = [
            AndreaniProvider(),
            CorreoArgentinoProvider()
        ]
        
        for provider in providers:
            try:
                rates = provider.calculate_rates(zip_code_val, weight=total_weight, dimensions=dimensions)
                results.extend(rates)
            except Exception as e:
                logger.error(f"Error en provider {type(provider).__name__}: {str(e)}")

        # 3. Fallbacks (si las APIs fallan o no están configuradas)
        has_andreani = any('andreani' in opt['id'] for opt in results)
        
        if not has_andreani:
            # Fallback a sucursal si no hay nada
            results.append({
                "id": "andreani_sucursal_fallback",
                "nombre": "Andreani (Retiro en Sucursal)",
                "costo": 5200 if zip_code_val < 3000 else 6800,
                "tiempo_estimado": "2 a 4 días hábiles"
            })
            results.append({
                "id": "andreani_domicilio_fallback",
                "nombre": "Andreani (Envío a Domicilio)",
                "costo": 6200 if zip_code_val < 3000 else 7900,
                "tiempo_estimado": "3 a 5 días hábiles"
            })

        # 4. Opción de Retiro en local (Río Cuarto)
        results.append({
            "id": "retiro_local",
            "nombre": "Retiro en Local (Río Cuarto)",
            "costo": 0,
            "tiempo_estimado": "Inmediato - Te avisaremos por WhatsApp"
        })
        
        # 5. Ordenar y devolver
        return sorted(results, key=lambda x: x['costo'])
