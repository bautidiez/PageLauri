from flask import Blueprint, request, jsonify, send_from_directory, current_app
from extensions import limiter
from cache_utils import cache, invalidate_cache, cached
from models import *
from sqlalchemy import or_, and_, desc
from datetime import datetime
import uuid
import os
import json
import logging
from services.product_service import ProductService
from services.order_service import OrderService

logger = logging.getLogger(__name__)
store_public_bp = Blueprint('store_public', __name__)

# ==================== PRODUCTOS ====================

@store_public_bp.route('/api/productos', methods=['GET'])
def get_productos():
    """Obtener productos con filtros y paginación (público) - REFACTORIZADO"""
    cache_key = f"productos:{request.query_string.decode()}"
    cached_result = cache.get(cache_key)
    if cached_result: return jsonify(cached_result), 200

    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 12, type=int)
    filters = request.args.to_dict()
    
    pagination = ProductService.get_catalog(filters, page, page_size)
    
    result = {
        'items': [p.to_dict() for p in pagination.items],
        'total': pagination.total,
        'page': page,
        'page_size': page_size,
        'pages': pagination.pages
    }
    
    cache.set(cache_key, result, ttl_seconds=300)
    return jsonify(result), 200

@store_public_bp.route('/api/productos/<int:id>', methods=['GET'])
def get_producto(id):
    """Obtener detalle de producto (público)"""
    producto = Producto.query.get_or_404(id)
    if not producto.activo:
        return jsonify({'error': 'Producto no disponible'}), 404
    return jsonify(producto.to_dict()), 200

# ==================== CATEGORÍAS ====================

@store_public_bp.route('/api/categorias', methods=['GET'])
@cached(ttl_seconds=3600)
def get_categorias():
    include_subs = request.args.get('incluir_subcategorias', 'true') == 'true'
    padre_id = request.args.get('categoria_padre_id', type=int)
    flat = request.args.get('flat', 'false') == 'true'
    
    query = Categoria.query
    if padre_id:
        query = query.filter_by(categoria_padre_id=padre_id)
    elif not flat:
        query = query.filter_by(categoria_padre_id=None)
        
    categorias = query.order_by(Categoria.orden).all()
    return jsonify([c.to_dict(include_subcategorias=include_subs) for c in categorias]), 200

@store_public_bp.route('/api/categorias/tree', methods=['GET'])
@cached(ttl_seconds=3600)
def get_categorias_tree():
    try:
        categorias_raiz = Categoria.query.filter_by(categoria_padre_id=None).order_by(Categoria.orden).all()
        return jsonify([c.get_arbol_completo() for c in categorias_raiz]), 200
    except Exception as e:
        logger.error(f"Error en Categorias Tree: {str(e)}")
        return jsonify({'error': 'Error generando el árbol de categorías'}), 500

# ==================== TALLES Y COLORES ====================

@store_public_bp.route('/api/talles', methods=['GET'])
@cached(ttl_seconds=3600)
def get_talles():
    talles = Talle.query.all()
    orden = {'S':1, 'M':2, 'L':3, 'XL':4, 'XXL':5, 'XXXL':6}
    talles_s = sorted(talles, key=lambda t: orden.get(t.nombre.upper(), 99))
    return jsonify([t.to_dict() for t in talles_s]), 200

@store_public_bp.route('/api/colores', methods=['GET'])
@cached(ttl_seconds=3600)
def get_colores():
    colores = Color.query.all()
    return jsonify([c.to_dict() for c in colores]), 200

# ==================== PROMOCIONES ====================

@store_public_bp.route('/api/promociones', methods=['GET'])
def get_promociones():
    ahora = datetime.utcnow()
    promos = PromocionProducto.query.filter(
        PromocionProducto.activa == True,
        PromocionProducto.fecha_inicio <= ahora,
        or_(PromocionProducto.fecha_fin.is_(None), PromocionProducto.fecha_fin >= ahora)
    ).all()
    return jsonify([p.to_dict() for p in promos]), 200

@store_public_bp.route('/api/promociones/validar', methods=['POST'])
def validar_cupon():
    """Valida un código de cupón y devuelve sus beneficios"""
    data = request.json
    codigo = data.get('codigo')
    
    if not codigo:
        return jsonify({'error': 'Código requerido'}), 400
        
    promo = PromocionProducto.query.filter_by(codigo=codigo, es_cupon=True, activa=True).first()
    
    if not promo or not promo.esta_activa():
        return jsonify({'error': 'Cupón inválido o vencido'}), 404
        
    if promo.max_usos is not None and promo.usos_actuales >= promo.max_usos:
        return jsonify({'error': 'Cupón agotado'}), 400
        
    return jsonify({
        'valido': True,
        'promo': promo.to_dict()
    }), 200

# ==================== CHECKOUT ====================

@store_public_bp.route('/api/pedidos', methods=['POST'])
@limiter.limit("3 per minute")
def create_pedido():
    data = request.get_json()
    try:
        pedido = OrderService.create_order(data)
        db.session.commit()
        return jsonify(pedido.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error Checkout: {str(e)}")
        return jsonify({'error': str(e)}), 400

@store_public_bp.route('/api/metodos-pago', methods=['GET'])
@cached(ttl_seconds=3600)
def get_metodos_pago():
    metodos = MetodoPago.query.filter_by(activo=True).all()
    return jsonify([m.to_dict() for m in metodos]), 200

@store_public_bp.route('/api/envios/calcular', methods=['POST'])
def calcular_envio_route():
    data = request.json
    # Lógica simplificada de cálculo
    return jsonify({'costo': 5500.0, 'metodo': data.get('metodo', 'estándar')}), 200

# ==================== CONTACTO ====================

@store_public_bp.route('/api/contacto', methods=['POST'])
@limiter.limit("2 per minute")
def enviar_contacto():
    data = request.json
    nombre, email, mensaje = data.get('nombre'), data.get('email'), data.get('mensaje')
    if not all([nombre, email, mensaje]): return jsonify({'error': 'Campos obligatorios'}), 400
    
    msg = Message(
        subject=f"Contacto Web: {nombre}",
        sender=current_app.config.get('MAIL_USERNAME'),
        recipients=[os.environ.get('CONTACT_EMAIL', 'tomasgomezz411@gmail.com')],
        body=f"Nombre: {nombre}\nEmail: {email}\nMensaje: {mensaje}",
        reply_to=email
    )
    try:
        mail.send(msg)
        return jsonify({'message': 'Ok'}), 200
    except Exception as e:
        return jsonify({'error': 'Error enviando'}), 500

# ==================== ESTÁTICOS ====================

@store_public_bp.route('/static/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)
