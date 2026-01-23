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

        # Asegurar que siempre haya una opción de "Correo" y "Andreani" si las APIs no devolvieron nada real
        has_andreani = any('andreani' in opt['id'] for opt in results)
        has_correo = any('correo_argentino' in opt['id'] for opt in results)
        
        if not has_correo:
            results.append({
                "id": "envio_estandar",
                "nombre": "Correo Argentino (Domicilio)",
                "costo": 5500 if zip_code_val < 2000 else 7500,
                "tiempo_estimado": "5 a 8 días hábiles"
            })
            results.append({
                "id": "correo_sucursal_fallback",
                "nombre": "Correo Argentino (Sucursal)",
                "costo": 4800 if zip_code_val < 2000 else 6600,
                "tiempo_estimado": "4 a 6 días hábiles"
            })
            
        if not has_andreani:
            results.append({
                "id": "andreani_domicilio_fallback",
                "nombre": "Andreani (Domicilio)",
                "costo": 5800 if zip_code_val < 2000 else 7900,
                "tiempo_estimado": "3 a 5 días hábiles"
            })

        # Opción siempre presente: Retiro en local
        if not any('retiro' in opt['id'] for opt in results):
            results.append({
                "id": "retiro_local",
                "nombre": "Retiro en Local (Gratis)",
                "costo": 0,
                "tiempo_estimado": "Inmediato - Te avisaremos por WhatsApp"
            })
        
        # Ordenar por costo para el cliente
        return sorted(results, key=lambda x: x['costo'])
