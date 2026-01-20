from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from extensions import limiter
from cache_utils import cache, invalidate_cache
from models import *
from sqlalchemy import func
from datetime import datetime, timedelta
import uuid
import os
import json
from PIL import Image
from pathlib import Path
from services.admin_service import AdminService

store_admin_bp = Blueprint('store_admin', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ==================== ESTADÍSTICAS ====================

@store_admin_bp.route('/api/admin/estadisticas', methods=['GET'])
@jwt_required()
def get_estadisticas():
    """Obtener estadísticas generales - REFACTORIZADO"""
    cache_key = "estadisticas:general_v3"
    cached_result = cache.get(cache_key)
    if cached_result: return jsonify(cached_result), 200
    
    try:
        stats = AdminService.get_dashboard_stats()
        cache.set(cache_key, stats, ttl_seconds=300)
        return jsonify(stats), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@store_admin_bp.route('/api/admin/estadisticas/ventas', methods=['GET'])
@jwt_required()
def get_estadisticas_ventas():
    """Obtener estadísticas de ventas por período - REFACTORIZADO"""
    periodo = request.args.get('periodo', 'dia')
    fecha_ref = request.args.get('fecha_referencia')
    
    cache_key = f"estadisticas_ventas_ref:{periodo}:{fecha_ref}"
    cached_result = cache.get(cache_key)
    if cached_result: return jsonify(cached_result), 200
    
    try:
        dt_ref = None
        if fecha_ref:
            dt_ref = datetime.strptime(fecha_ref, '%Y-%m-%d')
            
        stats = AdminService.get_sales_stats(periodo, dt_ref)
        cache.set(cache_key, stats, ttl_seconds=300)
        return jsonify(stats), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==================== PRODUCT SEARCH ====================

@store_admin_bp.route('/api/admin/products/search', methods=['GET'])
@jwt_required()
def search_products():
    """Search products for autocomplete/typeahead"""
    query = request.args.get('q', '').strip()
    
    if not query or len(query) < 2:
        return jsonify([]), 200
    
    try:
        # Search by name (case-insensitive)
        productos = Producto.query.filter(
            Producto.nombre.ilike(f'%{query}%'),
            Producto.activo == True
        ).limit(10).all()
        
        return jsonify([{
            'id': p.id,
            'nombre': p.nombre,
            'precio_base': p.precio_base,
            'precio_actual': p.get_precio_actual()
        } for p in productos]), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==================== CRUD ADMIN (PRODUCTOS) ====================

@store_admin_bp.route('/api/admin/productos', methods=['POST'])
@jwt_required()
def create_producto():
    data = request.get_json()
    if not data.get('nombre') or not data.get('categoria_id') or not data.get('precio'):
        return jsonify({'error': 'Faltan campos requeridos'}), 400
        
    producto = Producto(
        nombre=data['nombre'],
        descripcion=data.get('descripcion', ''),
        categoria_id=data['categoria_id'],
        precio=float(data['precio']),
        precio_oferta=data.get('precio_oferta'),
        destacado=data.get('destacado', False),
        activo=data.get('activo', True),
        tags=data.get('tags', ''),
        equipo=data.get('equipo', 'Boca Juniors'),
        liga=data.get('liga'),
        dorsal=data.get('dorsal'),
        numero=data.get('numero'),
        version=data.get('version'),
        marca=data.get('marca', 'Adidas')
    )
    db.session.add(producto)
    db.session.commit()
    invalidate_cache(pattern='productos')
    return jsonify(producto.to_dict()), 201

@store_admin_bp.route('/api/admin/productos/<int:id>', methods=['PUT', 'DELETE'])
@jwt_required()
def manage_product(id):
    producto = Producto.query.get_or_404(id)
    if request.method == 'DELETE':
        db.session.delete(producto)
        db.session.commit()
        invalidate_cache(pattern='productos')
        return jsonify({'message': 'Producto eliminado'}), 200
    
    data = request.get_json()
    producto.nombre = data.get('nombre', producto.nombre)
    producto.precio = float(data.get('precio', producto.precio))
    producto.activo = data.get('activo', producto.activo)
    # ... update more fields
    db.session.commit()
    invalidate_cache(pattern='productos')
    return jsonify(producto.to_dict()), 200

# ==================== STOCK ====================

@store_admin_bp.route('/api/admin/stock', methods=['GET', 'POST'])
@jwt_required()
def manage_stock():
    if request.method == 'POST':
        data = request.get_json()
        existing = StockTalle.query.filter_by(producto_id=data['producto_id'], talle_id=data['talle_id']).first()
        if existing:
            existing.cantidad = int(data['cantidad'])
        else:
            stock = StockTalle(producto_id=data['producto_id'], talle_id=data['talle_id'], cantidad=int(data['cantidad']))
            db.session.add(stock)
        db.session.commit()
        return jsonify({'message': 'Stock actualizado'}), 200
        
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 50, type=int)
    query = StockTalle.query.join(Producto).join(Talle)
    
    # Filter by producto_id if provided
    producto_id = request.args.get('producto_id', type=int)
    if producto_id:
        query = query.filter(StockTalle.producto_id == producto_id)
    
    search = request.args.get('search')
    if search:
        query = query.filter(Producto.nombre.ilike(f"%{search}%"))
        
    solo_bajo = request.args.get('solo_bajo')
    if solo_bajo == 'true':
        query = query.filter(StockTalle.cantidad <= 5)
        
    pagination = query.paginate(page=page, per_page=page_size)
    return jsonify({'items': [s.to_dict() for s in pagination.items], 'total': pagination.total, 'pages': pagination.pages, 'page': page}), 200

# ==================== IMAGES ====================

@store_admin_bp.route('/api/admin/productos/<int:producto_id>/imagenes', methods=['POST'])
@jwt_required()
def upload_imagen(producto_id):
    if 'imagen' not in request.files: return jsonify({'error': 'No file'}), 400
    file = request.files['imagen']
    if file and allowed_file(file.filename):
        try:
            filename = secure_filename(file.filename)
            unique_id = uuid.uuid4()
            
            # Procesar con PIL para convertir a WebP y optimizar
            img = Image.open(file)
            
            # Redimensionar si es necesario (max 1200px)
            if img.width > 1200 or img.height > 1200:
                img.thumbnail((1200, 1200), Image.Resampling.LANCZOS)
                
            webp_filename = f"{unique_id}.webp"
            filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], webp_filename)
            
            # Guardar como WebP optimizado
            img.save(filepath, 'WEBP', quality=85)
            
            imagen = ImagenProducto(
                producto_id=producto_id, 
                url=f"/static/uploads/{webp_filename}", 
                es_principal=request.form.get('es_principal')=='true'
            )
            db.session.add(imagen)
            db.session.commit()
            return jsonify(imagen.to_dict()), 201
        except Exception as e:
            logger.error(f"Error processing image: {e}")
            return jsonify({'error': 'Error al procesar la imagen'}), 500
    return jsonify({'error': 'Invalid file'}), 400

@store_admin_bp.route('/api/admin/imagenes/<int:imagen_id>', methods=['DELETE'])
@jwt_required()
def delete_imagen(imagen_id):
    imagen = ImagenProducto.query.get_or_404(imagen_id)
    db.session.delete(imagen)
    db.session.commit()
    return jsonify({'message': 'Deleted'}), 200

# ==================== PEDIDOS ====================

@store_admin_bp.route('/api/admin/pedidos', methods=['GET'])
@jwt_required()
def get_all_pedidos():
    """Lista todos los pedidos con filtros opcionales"""
    try:
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 50, type=int)
        estado = request.args.get('estado')
        aprobado = request.args.get('aprobado')
        
        query = Pedido.query
        
        if estado:
            query = query.filter_by(estado=estado)
        
        if aprobado is not None:
            # Convertir string a boolean
            aprobado_bool = aprobado.lower() == 'true'
            query = query.filter_by(aprobado=aprobado_bool)
        
        # Ordenar por más recientes primero
        query = query.order_by(Pedido.created_at.desc())
        
        pagination = query.paginate(page=page, per_page=page_size, error_out=False)
        
        return jsonify({
            'items': [p.to_dict() for p in pagination.items],
            'total': pagination.total,
            'page': page,
            'page_size': page_size,
            'pages': pagination.pages
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@store_admin_bp.route('/api/admin/pedidos/<int:pedido_id>', methods=['GET'])
@jwt_required()
def get_pedido_detalle(pedido_id):
    """Obtiene el detalle completo de un pedido"""
    try:
        pedido = Pedido.query.get_or_404(pedido_id)
        return jsonify(pedido.to_dict()), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 404

@store_admin_bp.route('/api/admin/pedidos/<int:pedido_id>', methods=['PATCH', 'PUT'])
@jwt_required()
def update_pedido_estado(pedido_id):
    """Actualiza el estado de un pedido"""
    try:
        pedido = Pedido.query.get_or_404(pedido_id)
        data = request.get_json()
        
        if 'estado' in data:
            pedido.estado = data['estado']
        
        db.session.commit()
        invalidate_cache(pattern='estadisticas')
        
        return jsonify(pedido.to_dict()), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@store_admin_bp.route('/api/admin/pedidos/pendientes', methods=['GET'])
@jwt_required()
def get_pedidos_pendientes():
    """Obtiene pedidos pendientes de aprobación"""
    try:
        pedidos = Pedido.query.filter_by(
            aprobado=False,
            estado='pendiente_aprobacion'
        ).order_by(Pedido.created_at.desc()).all()
        
        return jsonify([p.to_dict() for p in pedidos]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@store_admin_bp.route('/api/admin/pedidos/<int:pedido_id>/aprobar', methods=['POST'])
@jwt_required()
def aprobar_pedido(pedido_id):
    """
    Aprueba un pedido y ejecuta el procesamiento:
    - Marca como aprobado
    - Reduce stock
    - Incrementa contador de ventas
    - Cambia estado a 'confirmado'
    """
    try:
        pedido = Pedido.query.get_or_404(pedido_id)
        
        # Validaciones
        if pedido.aprobado:
            return jsonify({'error': 'El pedido ya está aprobado'}), 400
        
        if pedido.fecha_expiracion and pedido.fecha_expiracion < datetime.utcnow():
            return jsonify({'error': 'El pedido ha expirado y no puede ser aprobado'}), 400
        
        # Verificar stock disponible antes de aprobar
        for item in pedido.items:
            stock_talle = StockTalle.query.filter_by(
                producto_id=item.producto_id,
                talle_id=item.talle_id
            ).first()
            
            if not stock_talle or stock_talle.cantidad < item.cantidad:
                producto = Producto.query.get(item.producto_id)
                talle = Talle.query.get(item.talle_id)
                return jsonify({
                    'error': f'Stock insuficiente para {producto.nombre} talle {talle.nombre}'
                }), 400
        
        # Obtener admin que aprueba
        admin_identity = get_jwt_identity()
        admin = Admin.query.filter_by(username=admin_identity).first()
        
        # Aprobar pedido
        pedido.aprobado = True
        pedido.fecha_aprobacion = datetime.utcnow()
        pedido.admin_aprobador_id = admin.id if admin else None
        pedido.estado = 'confirmado'
        
        # Reducir stock y actualizar ventas
        for item in pedido.items:
            stock_talle = StockTalle.query.filter_by(
                producto_id=item.producto_id,
                talle_id=item.talle_id
            ).first()
            
            if stock_talle:
                stock_talle.reducir_stock(item.cantidad)
            
            producto = Producto.query.get(item.producto_id)
            if producto:
                producto.ventas_count = (producto.ventas_count or 0) + item.cantidad
        
        db.session.commit()
        
        # Invalidar caches relevantes
        invalidate_cache(pattern='estadisticas')
        invalidate_cache(pattern='productos')
        
        # TODO: Enviar notificaciones al cliente (email/WhatsApp)
        # from services.notification_service import NotificationService
        # NotificationService.notificar_pedido_aprobado(pedido)
        
        return jsonify({
            'message': 'Pedido aprobado exitosamente',
            'pedido': pedido.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Endpoints de notas internas (ya existían en el plan original)
@store_admin_bp.route('/api/admin/pedidos/<int:pedido_id>/notas', methods=['GET', 'POST'])
@jwt_required()
def manage_notas_pedido(pedido_id):
    """Gestiona las notas internas de un pedido"""
    pedido = Pedido.query.get_or_404(pedido_id)
    
    if request.method == 'GET':
        notas = NotaPedido.query.filter_by(pedido_id=pedido_id).order_by(NotaPedido.created_at.desc()).all()
        return jsonify([n.to_dict() for n in notas]), 200
    
    # POST - Agregar nueva nota
    data = request.get_json()
    admin_identity = get_jwt_identity()
    admin = Admin.query.filter_by(username=admin_identity).first()
    
    if not admin:
        return jsonify({'error': 'Admin no encontrado'}), 404
    
    nota = NotaPedido(
        pedido_id=pedido_id,
        admin_id=admin.id,
        contenido=data.get('contenido', '')
    )
    
    db.session.add(nota)
    db.session.commit()
    
    return jsonify(nota.to_dict()), 201

@store_admin_bp.route('/api/admin/notas/<int:nota_id>', methods=['DELETE'])
@jwt_required()
def delete_nota(nota_id):
    """Elimina una nota interna"""
    nota = NotaPedido.query.get_or_404(nota_id)
    db.session.delete(nota)
    db.session.commit()
    return jsonify({'message': 'Nota eliminada'}), 200

# ==================== VENTAS EXTERNAS ====================

@store_admin_bp.route('/api/admin/ventas-externas', methods=['POST'])
@jwt_required()
def crear_venta_externa():
    """
    Registra una venta externa (realizada fuera de la tienda web)
    - Valida stock disponible
    - Reduce stock
    - Incrementa contador de ventas del producto
    - Calcula y guarda ganancia total
    """
    try:
        data = request.get_json()
        
        # Validaciones
        required_fields = ['producto_id', 'talle_id', 'cantidad', 'precio_unitario']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Campo requerido: {field}'}), 400
        
        producto_id = int(data['producto_id'])
        talle_id = int(data['talle_id'])
        cantidad = int(data['cantidad'])
        precio_unitario = float(data['precio_unitario'])
        
        if cantidad <= 0:
            return jsonify({'error': 'La cantidad debe ser mayor a 0'}), 400
        
        if precio_unitario <= 0:
            return jsonify({'error': 'El precio unitario debe ser mayor a 0'}), 400
        
        # Verificar que el producto y talle existen
        producto = Producto.query.get(producto_id)
        if not producto:
            return jsonify({'error': 'Producto no encontrado'}), 404
        
        talle = Talle.query.get(talle_id)
        if not talle:
            return jsonify({'error': 'Talle no encontrado'}), 404
        
        # Verificar stock disponible
        stock_talle = StockTalle.query.filter_by(
            producto_id=producto_id,
            talle_id=talle_id
        ).first()
        
        if not stock_talle or stock_talle.cantidad < cantidad:
            return jsonify({
                'error': f'Stock insuficiente para {producto.nombre} talle {talle.nombre}. Disponible: {stock_talle.cantidad if stock_talle else 0}'
            }), 400
        
        # Obtener admin que registra la venta
        admin_identity = get_jwt_identity()
        admin = Admin.query.filter_by(username=admin_identity).first()
        
        if not admin:
            return jsonify({'error': 'Admin no encontrado'}), 404
        
        # Calcular ganancia total
        ganancia_total = cantidad * precio_unitario
        
        # Crear venta externa
        venta = VentaExterna(
            producto_id=producto_id,
            talle_id=talle_id,
            cantidad=cantidad,
            precio_unitario=precio_unitario,
            ganancia_total=ganancia_total,
            fecha=datetime.utcnow(),
            admin_id=admin.id,
            notas=data.get('notas', '')
        )
        
        # Reducir stock
        stock_talle.reducir_stock(cantidad)
        
        # Incrementar contador de ventas del producto
        producto.ventas_count = (producto.ventas_count or 0) + cantidad
        
        db.session.add(venta)
        db.session.commit()
        
        # Invalidar caches relevantes
        invalidate_cache(pattern='estadisticas')
        invalidate_cache(pattern='productos')
        
        return jsonify({
            'message': 'Venta externa registrada exitosamente',
            'venta': venta.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@store_admin_bp.route('/api/admin/ventas-externas', methods=['GET'])
@jwt_required()
def listar_ventas_externas():
    """
    Lista ventas externas con paginación y filtros opcionales
    Filtros: producto_id, fecha_desde, fecha_hasta
    """
    try:
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 50, type=int)
        producto_id = request.args.get('producto_id', type=int)
        fecha_desde = request.args.get('fecha_desde')
        fecha_hasta = request.args.get('fecha_hasta')
        
        query = VentaExterna.query
        
        # Filtrar por producto
        if producto_id:
            query = query.filter_by(producto_id=producto_id)
        
        # Filtrar por rango de fechas
        if fecha_desde:
            fecha_desde_dt = datetime.strptime(fecha_desde, '%Y-%m-%d')
            query = query.filter(VentaExterna.fecha >= fecha_desde_dt)
        
        if fecha_hasta:
            fecha_hasta_dt = datetime.strptime(fecha_hasta, '%Y-%m-%d')
            # Incluir todo el día hasta las 23:59:59
            fecha_hasta_dt = fecha_hasta_dt.replace(hour=23, minute=59, second=59)
            query = query.filter(VentaExterna.fecha <= fecha_hasta_dt)
        
        # Ordenar por fecha más reciente primero
        query = query.order_by(VentaExterna.fecha.desc())
        
        pagination = query.paginate(page=page, per_page=page_size, error_out=False)
        
        return jsonify({
            'items': [v.to_dict() for v in pagination.items],
            'total': pagination.total,
            'page': page,
            'page_size': page_size,
            'pages': pagination.pages
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@store_admin_bp.route('/api/admin/ventas-externas/<int:venta_id>', methods=['DELETE'])
@jwt_required()
def eliminar_venta_externa(venta_id):
    """
    Elimina una venta externa y restaura el stock
    También decrementa el contador de ventas del producto
    """
    try:
        venta = VentaExterna.query.get_or_404(venta_id)
        
        # Restaurar stock
        stock_talle = StockTalle.query.filter_by(
            producto_id=venta.producto_id,
            talle_id=venta.talle_id
        ).first()
        
        if stock_talle:
            stock_talle.aumentar_stock(venta.cantidad)
        
        # Decrementar contador de ventas del producto
        producto = Producto.query.get(venta.producto_id)
        if producto and producto.ventas_count:
            producto.ventas_count = max(0, producto.ventas_count - venta.cantidad)
        
        db.session.delete(venta)
        db.session.commit()
        
        # Invalidar caches relevantes
        invalidate_cache(pattern='estadisticas')
        invalidate_cache(pattern='productos')
        
        return jsonify({'message': 'Venta externa eliminada y stock restaurado'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
