import requests
import os
import logging

logger = logging.getLogger(__name__)

class BaseShippingProvider:
    def calculate_rates(self, zip_code, weight=1.0, volumes=None):
        raise NotImplementedError("Each provider must implement calculate_rates")

class AndreaniProvider(BaseShippingProvider):
    def __init__(self):
        self.credential_id = os.environ.get('ANDREANI_CREDENTIAL_ID')
        self.api_url = os.environ.get('ANDREANI_API_URL', 'https://api.andreani.com')
        # Estos se necesitarán del usuario para tarifas reales
        self.cliente = os.environ.get('ANDREANI_CLIENTE')
        self.contrato_domicilio = os.environ.get('ANDREANI_CONTRATO_DOMICILIO')
        self.contrato_sucursal = os.environ.get('ANDREANI_CONTRATO_SUCURSAL')

    def calculate_rates(self, zip_code, weight=1.0, volumes=None):
        if not self.credential_id:
            logger.warning("Andreani credential ID not configured")
            return []
            
        if not self.cliente or (not self.contrato_domicilio and not self.contrato_sucursal):
            logger.warning("Andreani CLIENTE or CONTRATO not configured. Using dummy values for testing.")
            # Dummy values used during testing that returned 200
            cliente = self.cliente or "CL0003750"
            contratos = {
                "andreani_sucursal": self.contrato_sucursal or "400006709",
                "andreani_domicilio": self.contrato_domicilio or "400006710" 
            }
        else:
            cliente = self.cliente
            contratos = {}
            if self.contrato_sucursal: contratos["andreani_sucursal"] = self.contrato_sucursal
            if self.contrato_domicilio: contratos["andreani_domicilio"] = self.contrato_domicilio

        results = []
        headers = {'X-Authorization-Id': self.credential_id}
        
        for method_id, contrato in contratos.items():
            try:
                # El endpoint v1/tarifas requiere GET con parámetros indexados
                params = {
                    "cpDestino": str(zip_code),
                    "contrato": contrato,
                    "cliente": cliente,
                    "bultos[0][valorDeclarado]": "1000", # Valor base
                    "bultos[0][volumen]": "0.02", # Volumen base
                    "bultos[0][kilos]": str(weight)
                }
                
                response = requests.get(f"{self.api_url}/v1/tarifas", params=params, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    costo_total = float(data.get('tarifaConIva', {}).get('total', 0))
                    
                    if costo_total > 0:
                        nombre = "Andreani (Sucursal)" if "sucursal" in method_id else "Andreani (Domicilio)"
                        results.append({
                            "id": method_id,
                            "nombre": nombre,
                            "costo": int(costo_total),
                            "tiempo_estimado": "3 a 5 días hábiles"
                        })
                else:
                    logger.error(f"Error Andreani API ({method_id}): {response.status_code} - {response.text}")
                    
            except Exception as e:
                logger.error(f"Excepción en Andreani ({method_id}): {str(e)}")
                
        return results

class CorreoArgentinoProvider(BaseShippingProvider):
    def __init__(self):
        self.user = os.environ.get('CORREO_ARG_USER')
        self.password = os.environ.get('CORREO_ARG_PASS')
        self.customer_id = os.environ.get('CORREO_ARG_CUSTOMER_ID')
        self.api_base = "https://api.correoargentino.com.ar/micorreo/v1"

    def _get_token(self):
        if not self.user or not self.password:
            return None
        try:
            auth = (self.user, self.password)
            response = requests.post(f"{self.api_base}/token", auth=auth, timeout=10)
            if response.status_code == 200:
                return response.json().get('token')
            else:
                logger.error(f"Error Correo Arg Auth: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            logger.error(f"Excepción en Correo Arg Auth: {str(e)}")
            return None

    def calculate_rates(self, zip_code, weight=1.0, volumes=None):
        token = self._get_token()
        if not token or not self.customer_id:
            logger.warning("Correo Argentino credentials or Customer ID not configured")
            return []

        results = []
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # Origin ZIP should be configured or default (example 1406)
        origin_zip = os.environ.get('ORIGIN_ZIP', '1406')

        payload = {
            "customerId": self.customer_id,
            "postalCodeOrigin": origin_zip,
            "postalCodeDestination": str(zip_code),
            "dimensions": {
                "weight": int(weight * 1000), # gramos
                "height": 10,
                "width": 10,
                "length": 10
            }
        }

        try:
            response = requests.post(f"{self.api_base}/rates", json=payload, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                rates = data.get('rates', [])
                for rate in rates:
                    tipo = rate.get('deliveredType')
                    nombre = "Correo Argentino (Domicilio)" if tipo == 'D' else "Correo Argentino (Sucursal)"
                    results.append({
                        "id": f"correo_argentino_{'domicilio' if tipo == 'D' else 'sucursal'}",
                        "nombre": nombre,
                        "costo": int(rate.get('price', 0)),
                        "tiempo_estimado": f"{rate.get('deliveryTimeMin', 3)}-{rate.get('deliveryTimeMax', 6)} días hábiles"
                    })
            else:
                logger.error(f"Error Correo Arg Rates: {response.status_code} - {response.text}")
        except Exception as e:
            logger.error(f"Excepción en Correo Arg Rates: {str(e)}")

        return results

class TiendaNubeProvider(BaseShippingProvider):
    def calculate_rates(self, zip_code, weight=1.0, volumes=None):
        # Tienda Nube no es un transportista per se, sino una plataforma.
        # Si el usuario quiere "Enviar por Tienda Nube", puede ser un método personalizado 
        # o integración con sus gateways de envío vinculados.
        return [
            {
                "id": "tienda_nube_envio",
                "nombre": "Envíos Tienda Nube",
                "costo": 4500,
                "tiempo_estimado": "Depende del transportista seleccionado en panel"
            }
        ]
