import requests
import os

class PaymentService:
    @staticmethod
    def create_mercadopago_preference(pedido):
        """Crea una preferencia de pago en Mercado Pago para el pedido"""
        access_token = os.environ.get('MP_ACCESS_TOKEN')
        if not access_token:
            print("ERROR: MP_ACCESS_TOKEN no configurado.")
            return None
            
        url = "https://api.mercadopago.com/checkout/preferences"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        # Preparar items
        items = []
        for item in pedido.items:
            items.append({
                "title": item.producto_nombre,
                "unit_price": float(item.precio_unitario),
                "quantity": item.cantidad,
                "currency_id": "ARS"
            })
            
        # Agregar costo de envío como un item si existe
        if pedido.costo_envio > 0:
            items.append({
                "title": "Costo de Envío",
                "unit_price": float(pedido.costo_envio),
                "quantity": 1,
                "currency_id": "ARS"
            })

        payload = {
            "items": items,
            "payer": {
                "name": pedido.cliente_nombre,
                "email": pedido.cliente_email
            },
            "back_urls": {
                "success": "http://localhost:4200/checkout/success",
                "failure": "http://localhost:4200/checkout/failure",
                "pending": "http://localhost:4200/checkout/pending"
            },
            "auto_return": "approved",
            "external_reference": str(pedido.id),
            "notification_url": os.environ.get('WEBHOOK_BASE_URL', '') + "/api/payments/webhook"
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers)
            if response.status_code == 201:
                pref = response.json()
                pedido.external_id = pref['id'] # Guardar ID de preferencia
                return pref['init_point'] # Retornar link de pago
            return None
        except Exception as e:
            print(f"Error Mercado Pago: {e}")
            return None

    @staticmethod
    def get_transfer_data():
        """Retorna datos para transferencia bancaria"""
        return {
            "banco": os.environ.get('BANCO_NOMBRE', 'Banco Galicia'),
            "cbu": os.environ.get('BANCO_CBU', '0000000000000000000000'),
            "alias": os.environ.get('BANCO_ALIAS', 'pago.lauri.tienda'),
            "titular": os.environ.get('BANCO_TITULAR', 'PagLauri S.R.L.')
        }
