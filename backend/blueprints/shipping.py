from flask import Blueprint, request, jsonify
from services.shipping_service import ShippingService

shipping_bp = Blueprint('shipping', __name__)

@shipping_bp.route('/calculate', methods=['POST'])
def calculate_shipping():
    data = request.json
    zip_code = data.get('codigo_postal')
    
    if not zip_code:
        return jsonify({"error": "Código postal es requerido"}), 400
        
    try:
        options = ShippingService.calculate_cost(zip_code)
        return jsonify(options), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
