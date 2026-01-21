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
import logging

logger = logging.getLogger(__name__)

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
    """Obtener estadísticas de ventas por período - REFACTORIZADO CON NUEVOS PARÁMETROS"""
    periodo = request.args.get('periodo', 'dia')
    fecha_ref = request.args.get('fecha_referencia')
    semana_offset = int(request.args.get('semana_offset', 0))  # Para navegación de semanas
    anio = request.args.get('anio')  # Para mes y semana
    if anio:
        anio = int(anio)
    
    cache_key = f"estadisticas_ventas:{periodo}:{fecha_ref}:{semana_offset}:{anio}"
    cached_result = cache.get(cache_key)
    if cached_result: return jsonify(cached_result), 200
    
    try:
        dt_ref = None
        if fecha_ref:
            dt_ref = datetime.strptime(fecha_ref, '%Y-%m-%d')
            
        stats = AdminService.get_sales_stats(periodo, dt_ref, semana_offset, anio)
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
            Producto.nombre.ilike(f'%{query}%')
        ).limit(20).all()
        
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
    if not data.get('nombre') or not data.get('categoria_id') or not data.get('precio_base'):
        return jsonify({'error': 'Faltan campos requeridos (nombre, categoria_id, precio_base)'}), 400
        
    try:
        producto = Producto(
            nombre=data['nombre'],
            descripcion=data.get('descripcion', ''),
            categoria_id=int(data['categoria_id']),
            precio_base=float(data['precio_base']),
            precio_descuento=float(data['precio_descuento']) if data.get('precio_descuento') else None,
            destacado=data.get('destacado', False),
            activo=data.get('activo', True),
            color=data.get('color'),
            color_hex=data.get('color_hex'),
            dorsal=data.get('dorsal'),
            numero=int(data['numero']) if data.get('numero') is not None and data.get('numero') != '' else None,
            version=data.get('version'),
            producto_relacionado_id=int(data['producto_relacionado_id']) if data.get('producto_relacionado_id') else None
        )
        db.session.add(producto)
        db.session.commit()
        invalidate_cache(pattern='productos')
        return jsonify(producto.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@store_admin_bp.route('/api/admin/productos/<int:id>', methods=['PUT', 'DELETE'])
@jwt_required()
def manage_product(id):
    producto = Producto.query.get_or_404(id)
    if request.method == 'DELETE':
        try:
            db.session.delete(producto)
            db.session.commit()
            invalidate_cache(pattern='productos')
            return jsonify({'message': 'Producto eliminado'}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500
    
    data = request.get_json()
    try:
        if 'nombre' in data: producto.nombre = data['nombre']
        if 'descripcion' in data: producto.descripcion = data['descripcion']
        if 'precio_base' in data: producto.precio_base = float(data['precio_base'])
        if 'precio_descuento' in data: 
            producto.precio_descuento = float(data['precio_descuento']) if data['precio_descuento'] else None
        if 'categoria_id' in data: producto.categoria_id = int(data['categoria_id'])
        if 'activo' in data: producto.activo = data['activo']
        if 'destacado' in data: producto.destacado = data['destacado']
        if 'color' in data: producto.color = data['color']
        if 'color_hex' in data: producto.color_hex = data['color_hex']
        if 'dorsal' in data: producto.dorsal = data['dorsal']
        if 'numero' in data: 
            producto.numero = int(data['numero']) if data['numero'] is not None and data['numero'] != '' else None
        if 'version' in data: producto.version = data['version']
        if 'producto_relacionado_id' in data:
            producto.producto_relacionado_id = int(data['producto_relacionado_id']) if data['producto_relacionado_id'] else None
            
        db.session.commit()
        invalidate_cache(pattern='productos')
        return jsonify(producto.to_dict()), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# ==================== CATEGORÍAS (ADMIN) ====================

@store_admin_bp.route('/api/admin/categorias', methods=['POST'])
@jwt_required()
def create_categoria():
    data = request.get_json()
    if not data.get('nombre'):
        return jsonify({'error': 'Nombre es requerido'}), 400
        
    try:
        # Sanatizar categoria_padre_id (puede venir como string vacío o null)
        padre_id = data.get('categoria_padre_id')
        if padre_id == '' or padre_id == 'null' or padre_id == 0:
            padre_id = None
        else:
            try:
                padre_id = int(padre_id)
            except (ValueError, TypeError):
                padre_id = None

        categoria = Categoria(
            nombre=data['nombre'],
            descripcion=data.get('descripcion', ''),
            imagen=data.get('imagen'),
            categoria_padre_id=padre_id,
            orden=int(data.get('orden', 0)),
            activa=data.get('activa', True),
            slug=data.get('slug')
        )
        db.session.add(categoria)
        
        # Opcional: Procesar subcategorías nuevas si vienen en el payload
        if 'subcategorias_nuevas' in data:
            for sub_data in data['subcategorias_nuevas']:
                sub_cat = Categoria(
                    nombre=sub_data['nombre'],
                    descripcion=sub_data.get('descripcion', ''),
                    categoria_padre=categoria, # Relación directa
                    orden=int(sub_data.get('orden', 0)),
                    activa=sub_data.get('activa', True)
                )
                db.session.add(sub_cat)

        db.session.commit()
        invalidate_cache(pattern='categorias')
        return jsonify(categoria.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@store_admin_bp.route('/api/admin/categorias/<int:id>', methods=['PUT', 'DELETE'])
@jwt_required()
def manage_category(id):
    categoria = Categoria.query.get_or_404(id)
    
    if request.method == 'DELETE':
        force = request.args.get('force', 'false') == 'true'
        try:
            if not force and categoria.productos:
                return jsonify({'error': 'La categoría tiene productos asociados. Use force=true para borrar.'}), 400
            db.session.delete(categoria)
            db.session.commit()
            invalidate_cache(pattern='categorias')
            return jsonify({'message': 'Categoría eliminada'}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500
            
    data = request.get_json()
    try:
        if 'nombre' in data: categoria.nombre = data['nombre']
        if 'descripcion' in data: categoria.descripcion = data['descripcion']
        if 'imagen' in data: categoria.imagen = data['imagen']
        if 'categoria_padre_id' in data: 
            padre_id = data['categoria_padre_id']
            if padre_id == '' or padre_id == 'null' or padre_id == 0:
                categoria.categoria_padre_id = None
            else:
                try:
                    categoria.categoria_padre_id = int(padre_id)
                except (ValueError, TypeError):
                    categoria.categoria_padre_id = None
                    
        if 'orden' in data: categoria.orden = int(data['orden'])
        if 'activa' in data: categoria.activa = data['activa']
        if 'slug' in data: categoria.slug = data['slug']
        
        db.session.commit()
        invalidate_cache(pattern='categorias')
        return jsonify(categoria.to_dict()), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# ==================== STOCK ====================

@store_admin_bp.route('/api/admin/stock', methods=['GET', 'POST'])
@jwt_required()
def manage_stock():
    if request.method == 'POST':
        data = request.get_json()
        try:
            existing = StockTalle.query.filter_by(producto_id=data['producto_id'], talle_id=data['talle_id']).first()
            if existing:
                existing.cantidad = int(data['cantidad'])
                if 'color_id' in data: existing.color_id = data['color_id']
            else:
                stock = StockTalle(
                    producto_id=data['producto_id'], 
                    talle_id=data['talle_id'], 
                    cantidad=int(data['cantidad']),
                    color_id=data.get('color_id')
                )
                db.session.add(stock)
            db.session.commit()
            return jsonify({'message': 'Stock actualizado'}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500
        
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

@store_admin_bp.route('/api/admin/stock/<int:id>', methods=['PUT', 'DELETE'])
@jwt_required()
def manage_single_stock(id):
    stock = StockTalle.query.get_or_404(id)
    if request.method == 'DELETE':
        try:
            db.session.delete(stock)
            db.session.commit()
            return jsonify({'message': 'Stock eliminado'}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500
            
    data = request.get_json()
    try:
        if 'cantidad' in data:
            stock.cantidad = int(data['cantidad'])
        if 'color_id' in data:
            stock.color_id = data['color_id']
        if 'talle_id' in data:
            stock.talle_id = data['talle_id']
            
        db.session.commit()
        return jsonify(stock.to_dict()), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@store_admin_bp.route('/api/admin/stock/add', methods=['POST'])
@jwt_required()
def add_stock_by_sizes():
    """
    Incrementa el stock de un producto para múltiples talles.
    Recibe: { product_id: int, increments: { "S": 5, "M": 10, "L": 3 } }
    """
    try:
        data = request.get_json()
        product_id = data.get('product_id')
        increments = data.get('increments', {})
        
        if not product_id:
            return jsonify({'error': 'product_id es requerido'}), 400
        
        if not increments:
            return jsonify({'error': 'increments es requerido'}), 400
        
        # Verificar que el producto existe
        producto = Producto.query.get(product_id)
        if not producto:
            return jsonify({'error': 'Producto no encontrado'}), 404
        
        updated_sizes = []
        
        for size_name, quantity in increments.items():
            if quantity <= 0:
                continue
                
            # Buscar el talle por nombre
            talle = Talle.query.filter_by(nombre=size_name).first()
            if not talle:
                continue
            
            # Buscar stock existente o crear nuevo
            stock = StockTalle.query.filter_by(
                producto_id=product_id,
                talle_id=talle.id
            ).first()
            
            if stock:
                # Incrementar stock existente
                stock.cantidad += int(quantity)
            else:
                # Crear nuevo registro de stock
                stock = StockTalle(
                    producto_id=product_id,
                    talle_id=talle.id,
                    cantidad=int(quantity)
                )
                db.session.add(stock)
            
            updated_sizes.append({
                'talle': size_name,
                'nueva_cantidad': stock.cantidad
            })
        
        db.session.commit()
        
        return jsonify({
            'message': 'Stock actualizado exitosamente',
            'updated': updated_sizes
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

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
    admin_id = get_jwt_identity()
    admin = Admin.query.get(int(admin_id))
    
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
        admin_id = get_jwt_identity()
        admin = Admin.query.get(int(admin_id))
        
        if not admin:
            return jsonify({'error': 'Admin no encontrado (sesión inválida)'}), 404
        
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

# ==================== PROMOCIONES (ADMIN) ====================

@store_admin_bp.route('/api/admin/tipos-promocion', methods=['GET'])
@jwt_required()
def get_tipos_promocion():
    tipos = TipoPromocion.query.all()
    return jsonify([t.to_dict() for t in tipos]), 200

@store_admin_bp.route('/api/admin/promociones', methods=['POST'])
@jwt_required()
def create_promocion():
    data = request.get_json()
    try:
        promocion = PromocionProducto(
            alcance=data.get('alcance', 'producto'),
            tipo_promocion_id=data['tipo_promocion_id'],
            valor=float(data.get('valor', 0)),
            activa=data.get('activa', True),
            fecha_inicio=datetime.fromisoformat(data['fecha_inicio'].replace('Z', '+00:00')),
            fecha_fin=datetime.fromisoformat(data['fecha_fin'].replace('Z', '+00:00')),
            es_cupon=data.get('es_cupon', False),
            codigo=data.get('codigo'),
            envio_gratis=data.get('envio_gratis', False),
            compra_minima=float(data.get('compra_minima', 0))
        )
        
        # Vincular productos
        if data.get('productos_ids'):
            productos = Producto.query.filter(Producto.id.in_(data['productos_ids'])).all()
            promocion.productos = productos
            
        # Vincular categorías
        if data.get('categorias_ids'):
            categorias = Categoria.query.filter(Categoria.id.in_(data['categorias_ids'])).all()
            promocion.categorias = categorias
            
        db.session.add(promocion)
        db.session.commit()
        invalidate_cache(pattern='productos')
        return jsonify(promocion.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@store_admin_bp.route('/api/admin/promociones/<int:id>', methods=['PUT', 'DELETE'])
@jwt_required()
def manage_promocion(id):
    promocion = PromocionProducto.query.get_or_404(id)
    
    if request.method == 'DELETE':
        try:
            db.session.delete(promocion)
            db.session.commit()
            invalidate_cache(pattern='productos')
            return jsonify({'message': 'Promoción eliminada'}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500
            
    data = request.get_json()
    try:
        if 'alcance' in data: promocion.alcance = data['alcance']
        if 'tipo_promocion_id' in data: promocion.tipo_promocion_id = data['tipo_promocion_id']
        if 'valor' in data: promocion.valor = float(data['valor'])
        if 'activa' in data: promocion.activa = data['activa']
        if 'fecha_inicio' in data: 
            promocion.fecha_inicio = datetime.fromisoformat(data['fecha_inicio'].replace('Z', '+00:00'))
        if 'fecha_fin' in data: 
            promocion.fecha_fin = datetime.fromisoformat(data['fecha_fin'].replace('Z', '+00:00'))
        if 'es_cupon' in data: promocion.es_cupon = data['es_cupon']
        if 'codigo' in data: promocion.codigo = data['codigo']
        if 'envio_gratis' in data: promocion.envio_gratis = data['envio_gratis']
        if 'compra_minima' in data: promocion.compra_minima = float(data['compra_minima'])
        
        # Actualizar vínculos
        if 'productos_ids' in data:
            productos = Producto.query.filter(Producto.id.in_(data['productos_ids'])).all()
            promocion.productos = productos
            
        if 'categorias_ids' in data:
            categorias = Categoria.query.filter(Categoria.id.in_(data['categorias_ids'])).all()
            promocion.categorias = categorias
            
        db.session.commit()
        invalidate_cache(pattern='productos')
        return jsonify(promocion.to_dict()), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# ==================== TALLES Y COLORES (ADMIN) ====================

@store_admin_bp.route('/api/admin/talles', methods=['POST'])
@jwt_required()
def create_talle():
    data = request.get_json()
    try:
        talle = Talle(nombre=data['nombre'], orden=data.get('orden', 0))
        db.session.add(talle)
        db.session.commit()
        return jsonify(talle.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@store_admin_bp.route('/api/admin/talles/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_talle(id):
    talle = Talle.query.get_or_404(id)
    try:
        db.session.delete(talle)
        db.session.commit()
        return jsonify({'message': 'Talle eliminado'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@store_admin_bp.route('/api/admin/colores', methods=['POST'])
@jwt_required()
def create_color():
    data = request.get_json()
    try:
        color = Color(nombre=data['nombre'], codigo_hex=data.get('codigo_hex'))
        db.session.add(color)
        db.session.commit()
        return jsonify(color.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
