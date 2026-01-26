import requests
import os
import logging

logger = logging.getLogger(__name__)

class BaseShippingProvider:
    def calculate_billable_weight(self, actual_weight, length, width, height, factor=5000):
        """Calcula el mayor entre peso real y peso volumétrico."""
        volumetric_weight = (length * width * height) / factor
        return max(actual_weight, volumetric_weight)

    def calculate_rates(self, zip_code, weight=1.0, dimensions=None):
        raise NotImplementedError("Each provider must implement calculate_rates")

class AndreaniProvider(BaseShippingProvider):
    def __init__(self):
        self.credential_id = os.environ.get('ANDREANI_CREDENTIAL_ID')
        self.api_url = os.environ.get('ANDREANI_API_URL', 'https://api.andreani.com')
        self.cliente = os.environ.get('ANDREANI_CLIENTE')
        self.contrato_domicilio = os.environ.get('ANDREANI_CONTRATO_DOMICILIO')
        self.contrato_sucursal = os.environ.get('ANDREANI_CONTRATO_SUCURSAL')

    def calculate_rates(self, zip_code, weight=1.0, dimensions=None):
        # Andreani usa factor 5000 para peso volumétrico
        dims = dimensions or {"length": 25, "width": 20, "height": 10}
        billable_weight = self.calculate_billable_weight(weight, dims['length'], dims['width'], dims['height'], 5000)
        
        if not self.credential_id:
            logger.warning("Andreani credential ID not configured")
            return []
            
        cliente = self.cliente or "CL0003750"
        contratos = {}
        if self.contrato_sucursal: contratos["andreani_sucursal"] = self.contrato_sucursal
        if self.contrato_domicilio: contratos["andreani_domicilio"] = self.contrato_domicilio
        
        if not contratos:
            contratos = {"andreani_sucursal": "400006709", "andreani_domicilio": "400006710"}

        results = []
        headers = {'X-Authorization-Id': self.credential_id}
        
        for method_id, contrato in contratos.items():
            try:
                params = {
                    "cpDestino": str(zip_code),
                    "contrato": contrato,
                    "cliente": cliente,
                    "bultos[0][valorDeclarado]": "5000",
                    "bultos[0][volumen]": str((dims['length'] * dims['width'] * dims['height']) / 1000000), # m3
                    "bultos[0][kilos]": str(round(billable_weight, 2))
                }
                
                response = requests.get(f"{self.api_url}/v1/tarifas", params=params, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    costo_total = float(data.get('tarifaConIva', {}).get('total', 0))
                    
                    if costo_total > 0:
                        # Aplicar un pequeño margen de seguridad (3%) y redondear
                        costo_final = int(costo_total * 1.03)
                        nombre = "Andreani (Sucursal)" if "sucursal" in method_id else "Andreani (Domicilio)"
                        results.append({
                            "id": method_id,
                            "nombre": nombre,
                            "costo": costo_final,
                            "tiempo_estimado": "2 a 4 días hábiles"
                        })
            except Exception as e:
                logger.error(f"Error Andreani API: {str(e)}")
                
        return results

class CorreoArgentinoProvider(BaseShippingProvider):
    def __init__(self):
        self.user = os.environ.get('CORREO_ARG_USER')
        self.password = os.environ.get('CORREO_ARG_PASS')
        self.customer_id = os.environ.get('CORREO_ARG_CUSTOMER_ID')
        self.api_base = "https://api.correoargentino.com.ar/micorreo/v1"

    def calculate_rates(self, zip_code, weight=1.0, dimensions=None):
        # Correo Argentino usa factor 6000
        dims = dimensions or {"length": 25, "width": 20, "height": 10}
        billable_weight = self.calculate_billable_weight(weight, dims['length'], dims['width'], dims['height'], 6000)
        
        # Lógica de rangos (Fallback o principal según config)
        # Precios estimados para e-commerce (ajustar según tarifario vigente)
        # Río Cuarto (Córdoba) a...
        distancia_factor = 1.0 if 5000 <= int(zip_code) < 6000 else 1.3 # Córdoba vs resto del país
        
        if billable_weight <= 1:
            base_price = 4800
        elif billable_weight <= 5:
            base_price = 6200
        elif billable_weight <= 10:
            base_price = 8500
        else:
            base_price = 12000

        costo_sucursal = int(base_price * distancia_factor)
        costo_domicilio = int(costo_sucursal * 1.25)

        return [
            {
                "id": "correo_argentino_sucursal",
                "nombre": "Correo Argentino (Sucursal)",
                "costo": costo_sucursal,
                "tiempo_estimado": "3 a 6 días hábiles"
            },
            {
                "id": "correo_argentino_domicilio",
                "nombre": "Correo Argentino (Domicilio)",
                "costo": costo_domicilio,
                "tiempo_estimado": "4 a 8 días hábiles"
            }
        ]

