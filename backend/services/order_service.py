from models import db, Pedido, ItemPedido, Producto, Talle, StockTalle, PromocionProducto
from datetime import datetime
import uuid

class OrderService:
    @staticmethod
    def create_order(data: dict):
        """
        Lógica de creación de pedido con validación de stock, promociones automáticas y cupones.
        """
        numero_pedido = f"PED-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"
        
        pedido = Pedido(
            numero_pedido=numero_pedido,
            cliente_nombre=data.get('cliente_nombre'),
            cliente_email=data.get('cliente_email'),
            cliente_telefono=data.get('cliente_telefono', ''),
            cliente_direccion=data.get('cliente_direccion'),
            cliente_codigo_postal=data.get('cliente_codigo_postal'),
            cliente_localidad=data.get('cliente_localidad'),
            cliente_provincia=data.get('cliente_provincia'),
            metodo_pago_id=int(data.get('metodo_pago_id')),
            metodo_envio=data.get('metodo_envio', 'correo_argentino'),
            estado='pendiente_aprobacion',
            aprobado=False,
            fecha_expiracion=datetime.now() + timedelta(days=5)
        )
        
        db.session.add(pedido)
        db.session.flush()
        
        subtotal_bruto = 0
        descuento_promo_automatica = 0
        
        # 1. Procesar Items y Promociones Automáticas
        for item_data in data.get('items', []):
            producto = Producto.query.get(item_data['producto_id'])
            talle = Talle.query.get(item_data['talle_id'])
            cantidad = int(item_data['cantidad'])
            
            stock_talle = StockTalle.query.filter_by(producto_id=producto.id, talle_id=talle.id).first()
            if not stock_talle or stock_talle.cantidad < cantidad:
                raise Exception(f"Stock insuficiente: {producto.nombre} ({talle.nombre})")
            
            precio_unitario = producto.get_precio_actual()
            subtotal_bruto += precio_unitario * cantidad
            
            # Promociones AUTOMÁTICAS (no cupones)
            promo_auto_descuento = 0
            promos_auto = PromocionProducto.query.filter_by(activa=True, es_cupon=False).all()
            for promo in promos_auto:
                if promo.esta_activa() and OrderService._is_promo_applicable(promo, producto):
                    promo_auto_descuento += promo.calcular_descuento(cantidad, precio_unitario)
            
            descuento_promo_automatica += promo_auto_descuento
            
            # NOTA: Stock y ventas_count se actualizarán cuando el pedido sea APROBADO por el admin
            # Actualizar stock
            # stock_talle.reducir_stock(cantidad)
            # producto.ventas_count = (producto.ventas_count or 0) + cantidad
            
            # Crear item inicial (el subtotal y descuento final se ajustarán si hay cupón)
            item = ItemPedido(
                pedido_id=pedido.id,
                producto_id=producto.id,
                talle_id=talle.id,
                cantidad=cantidad,
                precio_unitario=precio_unitario,
                descuento_aplicado=promo_auto_descuento,
                subtotal=(precio_unitario * cantidad) - promo_auto_descuento
            )
            db.session.add(item)
            
        # 2. Procesar Cupón (si existe)
        descuento_cupon = 0
        codigo_cupon = data.get('codigo_cupon')
        if codigo_cupon:
            cupon = PromocionProducto.query.filter_by(codigo=codigo_cupon, activa=True, es_cupon=True).first()
            if not cupon or not cupon.esta_activa():
                raise Exception("Cupón inválido o expirado")
            
            if cupon.max_usos is not None and cupon.usos_actuales >= cupon.max_usos:
                raise Exception("Cupón agotado")
                
            if subtotal_bruto < cupon.compra_minima:
                raise Exception(f"Monto mínimo para este cupón: ${cupon.compra_minima}")
            
            # Aplicar cupón por alcance
            for item in pedido.items:
                producto = Producto.query.get(item.producto_id)
                if OrderService._is_promo_applicable(cupon, producto):
                    desc = cupon.calcular_descuento(item.cantidad, item.precio_unitario)
                    item.descuento_aplicado += desc
                    item.subtotal -= desc
                    descuento_cupon += desc
            
            if descuento_cupon > 0:
                cupon.usos_actuales += 1
            else:
                raise Exception("El cupón no aplica a los productos en el carrito")

        pedido.subtotal = subtotal_bruto - descuento_promo_automatica - descuento_cupon
        pedido.descuento = descuento_promo_automatica + descuento_cupon
        pedido.total = pedido.subtotal + data.get('costo_envio', 0)
        
        return pedido

    @staticmethod
    def _is_promo_applicable(promo, producto):
        if promo.alcance == 'tienda': return True
        if promo.alcance == 'producto' and any(p.id == producto.id for p in promo.productos): return True
        if promo.alcance == 'categoria' and any(c.id == producto.categoria_id for c in promo.categorias): return True
        return False
