from .shipping_providers import AndreaniProvider, CorreoArgentinoProvider, TiendaNubeProvider
import logging

logger = logging.getLogger(__name__)

class ShippingService:
    @staticmethod
    def calculate_cost(zip_code, items=None):
        """
        Lógica para calcular costos de envío usando proveedores reales.
        """
        try:
            zip_code_val = int(zip_code)
        except ValueError:
            logger.error(f"ZIP code inválido: {zip_code}")
            return []

        results = []
        
        # Proveedores
        providers = [
            AndreaniProvider(),
            CorreoArgentinoProvider(),
            TiendaNubeProvider()
        ]
        
        for provider in providers:
            try:
                rates = provider.calculate_rates(zip_code_val)
                results.extend(rates)
            except Exception as e:
                logger.error(f"Error en provider {type(provider).__name__}: {str(e)}")

        # Opción siempre presente: Retiro en local
        results.append({
            "id": "retiro_local",
            "nombre": "Retiro en Local (Gratis)",
            "costo": 0,
            "tiempo_estimado": "Inmediato - Te avisaremos por WhatsApp"
        })
        
        # Ordenar por costo para el cliente
        return sorted(results, key=lambda x: x['costo'])
