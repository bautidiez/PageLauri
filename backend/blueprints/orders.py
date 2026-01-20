from flask import Blueprint, request, jsonify
from models import db, Pedido, ItemPedido, Producto, Shipment, TrackingUpdate
from datetime import datetime
import uuid

orders_bp = Blueprint('orders', __name__)

@orders_bp.route('', methods=['POST'])
def create_order():
    data = request.json
    try:
        # Generar número de pedido único
        numero_pedido = f"EV-{uuid.uuid4().hex[:8].upper()}"
        
        nuevo_pedido = Pedido(
            numero_pedido=numero_pedido,
            cliente_nombre=data['cliente_nombre'],
            cliente_email=data['cliente_email'],
            cliente_telefono=data.get('cliente_telefono'),
            cliente_direccion=f"{data['calle']} {data['altura']} {data.get('piso', '')}",
            cliente_codigo_postal=data['codigo_postal'],
            cliente_localidad=data['ciudad'],
            cliente_provincia=data['provincia'],
            metodo_pago_id=data.get('metodo_pago_id', 1), # Default o mapeado
            metodo_envio=data.get('metodo_envio'),
            subtotal=data['subtotal'],
            descuento=data.get('descuento', 0),
            costo_envio=data.get('costo_envio', 0),
            total=data['total'],
            estado='pendiente_aprobacion',
            aprobado=False,
            fecha_expiracion=datetime.utcnow() + timedelta(days=5),
            codigo_pago_unico=uuid.uuid4().hex[:6].upper() if data.get('metodo_pago') == 'transferencia' else None
        )

        # RECALCULO DE TOTAL EN BACKEND
        # 1. Recuperar información completa de productos y sus promociones
        items_por_promocion = {}
        items_sin_promocion = []
        
        # Mapa temporal para búsquedas rápidas
        # Nota: Idealmente haríamos una query 'IN' para traer todos los productos de una vez
        producto_ids = [item['producto_id'] for item in data['items']]
        productos_db = Producto.query.filter(Producto.id.in_(producto_ids)).all()
        productos_map = {p.id: p for p in productos_db}
        
        calculated_total = 0
        
        for item in data['items']:
            prod = productos_map.get(item['producto_id'])
            if not prod:
                continue # O lanzar error
                
            promos = prod.get_promociones_activas()
            if promos:
                promo = promos[0] # Tomamos la primera activa
                key = f"promo_{promo.id}"
                if key not in items_por_promocion:
                    items_por_promocion[key] = []
                
                # Agregar item con su cantidad y precio
                items_por_promocion[key].append({
                    'cantidad': item['cantidad'],
                    'precio_unitario': item['precio_unitario'],
                    'promo_tipo': promo.tipo_promocion.nombre.lower()
                })
            else:
                items_sin_promocion.append(item)
                
        # Calcular items sin promoción
        for item in items_sin_promocion:
            calculated_total += (item['precio_unitario'] * item['cantidad'])
            
        # Calcular items con promoción agrupada
        for key, group in items_por_promocion.items():
            # Aplanar precios
            prices = []
            promo_tipo = group[0]['promo_tipo']
            
            for item in group:
                for _ in range(item['cantidad']):
                    prices.append(item['precio_unitario'])
            
            # Ordenar descendente (pagamos los más caros)
            prices.sort(reverse=True)
            
            if '2x1' in promo_tipo:
                # Pagar indices 0, 2, 4...
                for i in range(len(prices)):
                    if i % 2 == 0:
                        calculated_total += prices[i]
            elif '3x2' in promo_tipo:
                # Pagar indices que NO sean 2, 5, 8... (indices base 0: 0, 1 pagados; 2 gratis)
                for i in range(len(prices)):
                    if (i + 1) % 3 != 0:
                        calculated_total += prices[i]
            else:
                # Fallback suma simple (o implementar descuentos porcentuales si fuera necesario)
                calculated_total += sum(prices)
        
        # Aplicar costo de envío
        calculated_total += data.get('costo_envio', 0)
        
        # Actualizar total en el objeto pedido
        # Nota: Podríamos validar si data['total'] coincide y loguear warning si no
        nuevo_pedido.total = calculated_total
        
        db.session.add(nuevo_pedido)
        
        # Agregar items
        for item in data['items']:
            item_pedido = ItemPedido(
                pedido=nuevo_pedido,
                producto_id=item['producto_id'],
                talle_id=item['talle_id'],
                cantidad=item['cantidad'],
                precio_unitario=item['precio_unitario'],
                subtotal=item['precio_unitario'] * item['cantidad']
            )
            db.session.add(item_pedido)
            
            # NOTA: Stock se reducirá cuando el pedido sea APROBADO por el admin
            # No se reduce en la creación para evitar reservas de pedidos no aprobados
            # st = StockTalle.query.filter_by(producto_id=item['producto_id'], talle_id=item['talle_id']).first()
            # if st: st.cantidad -= item['cantidad']

        # Crear envío inicial
        envio = Shipment(
            pedido=nuevo_pedido,
            transportista=data.get('metodo_envio', 'A convenir'),
            costo=data.get('costo_envio', 0),
            estado='preparando'
        )
        db.session.add(envio)
        
        db.session.commit()
        return jsonify(nuevo_pedido.to_dict()), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@orders_bp.route('/<int:id>', methods=['GET'])
def get_order(id):
    pedido = Pedido.query.get_or_404(id)
    return jsonify(pedido.to_dict())

@orders_bp.route('/by-customer/<string:email>', methods=['GET'])
def get_customer_orders(email):
    pedidos = Pedido.query.filter_by(cliente_email=email).order_by(Pedido.created_at.desc()).all()
    return jsonify([p.to_dict() for p in pedidos])

@orders_bp.route('/<int:id>/status', methods=['PATCH'])
def update_order_status(id):
    data = request.json
    pedido = Pedido.query.get_or_404(id)
    pedido.estado = data.get('estado', pedido.estado)
    
    # Si cambia a pagado, podríamos gatillar WhatsApp aquí o vía service
    
    db.session.commit()
    return jsonify(pedido.to_dict())

@orders_bp.route('/<int:id>/tracking', methods=['PATCH'])
def update_tracking(id):
    data = request.json
    pedido = Pedido.query.get_or_404(id)
    if pedido.envio:
        pedido.envio.numero_guia = data.get('numero_guia', pedido.envio.numero_guia)
        pedido.envio.estado = data.get('estado', pedido.envio.estado)
        
        # Agregar hit en el historial
        update = TrackingUpdate(
            shipment=pedido.envio,
            estado=pedido.envio.estado,
            descripcion=data.get('descripcion', f"Estado actualizado a {pedido.envio.estado}")
        )
        db.session.add(update)
        
    db.session.commit()
    return jsonify(pedido.to_dict())
