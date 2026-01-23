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

        # Asegurar que siempre haya una opción de "Correo" si las APIs no devolvieron nada real
        # (Andreani y Correo Argentino suelen devolver IDs específicos)
        has_real_carrier = any(opt['id'].startswith(('andreani', 'correo_argentino')) for opt in results)
        
        if not has_real_carrier:
            results.append({
                "id": "envio_estandar",
                "nombre": "Envío Estándar (Correo Argentino)",
                "costo": 5500 if zip_code_val < 2000 else 7500,
                "tiempo_estimado": "5 a 8 días hábiles"
            })
            
            # También agregamos Andreani Domicilio como fallback si no hay nada
            results.append({
                "id": "andreani_domicilio_fallback",
                "nombre": "Andreani (Domicilio)",
                "costo": 5800 if zip_code_val < 2000 else 7900,
                "tiempo_estimado": "4 a 6 días hábiles"
            })

        # Opción siempre presente: Retiro en local
        results.append({
            "id": "retiro_local",
            "nombre": "Retiro en Local (Gratis)",
            "costo": 0,
            "tiempo_estimado": "Inmediato - Te avisaremos por WhatsApp"
        })
        
        # Ordenar por costo para el cliente
        return sorted(results, key=lambda x: x['costo'])
