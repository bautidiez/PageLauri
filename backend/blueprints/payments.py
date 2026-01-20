from flask import Blueprint, request, jsonify
from models import db, Pedido
from services.payment_service import PaymentService
from services.notification_service import NotificationService
import requests
import os

payments_bp = Blueprint('payments', __name__)

@payments_bp.route('/transfer-data', methods=['GET'])
def get_transfer_data():
    return jsonify(PaymentService.get_transfer_data())

@payments_bp.route('/webhook', methods=['POST'])
def mercadopago_webhook():
    # Recibir notificación de Mercado Pago
    data = request.args
    topic = data.get('topic') or data.get('type')
    id = data.get('id') or data.get('data.id')
    
    if topic == 'payment':
        # Consultar estado del pago en Mercado Pago
        access_token = os.environ.get('MP_ACCESS_TOKEN')
        url = f"https://api.mercadopago.com/v1/payments/{id}"
        headers = {"Authorization": f"Bearer {access_token}"}
        
        try:
            res = requests.get(url, headers=headers)
            payment_info = res.json()
            
            if payment_info.get('status') == 'approved':
                external_ref = payment_info.get('external_reference')
                if external_ref:
                    pedido = Pedido.query.get(int(external_ref))
                    if pedido and pedido.estado != 'pagado':
                        pedido.estado = 'pagado'
                        db.session.commit()
                        
                        # Gatillar Notificación
                        NotificationService.send_payment_confirmation(pedido)
                        
            return jsonify({"status": "received"}), 200
        except Exception as e:
            print(f"Error Webhook: {e}")
            return jsonify({"error": str(e)}), 500
            
    return jsonify({"status": "ignored"}), 200

@payments_bp.route('/confirm-transfer/<int:order_id>', methods=['POST'])
def confirm_transfer(order_id):
    # Confirmación manual o subida de comprobante
    pedido = Pedido.query.get_or_404(order_id)
    pedido.estado = 'pagado' # En un flujo real, quizás 'en_verificacion'
    db.session.commit()
    
    NotificationService.send_payment_confirmation(pedido)
    return jsonify({"status": "success", "message": "Confirmación recibida"}), 200
