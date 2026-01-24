from models import db, Pedido, ItemPedido, Producto, Talle, StockTalle, PromocionProducto, MetodoPago
from datetime import datetime, timedelta
import uuid

class OrderService:
    @staticmethod
    def create_order(data: dict):
        """
        Lógica de creación de pedido con validación de stock, promociones automáticas y cupones.
        """
        metodo_pago_val = data.get('metodo_pago') or data.get('metodo_pago_id')
        metodo_pago_id = None
        
        if isinstance(metodo_pago_val, str) and not metodo_pago_val.isdigit():
            # Buscar ID por nombre
            metodo = MetodoPago.query.filter(MetodoPago.nombre.ilike(f"%{metodo_pago_val}%")).first()
            if metodo:
                metodo_pago_id = metodo.id
            else:
                # Fallback o asignar uno por defecto si no existe
                metodo_pago_id = 1
        else:
            metodo_pago_id = int(metodo_pago_val) if metodo_pago_val else 1

        # 1. Calcular Subtotal Real y Validar Stock (En Memoria)
        subtotal_calculado = 0
        descuento_promo_automatica_total = 0
        items_procesados = []

        for item_data in data.get('items', []):
            producto = Producto.query.get(item_data['producto_id'])
            talle = Talle.query.get(item_data['talle_id'])
            cantidad = int(item_data['cantidad'])
            
            if not producto or not talle:
                continue

            stock_talle = StockTalle.query.filter_by(producto_id=producto.id, talle_id=talle.id).first()
            if not stock_talle or stock_talle.cantidad < cantidad:
                raise Exception(f"Stock insuficiente: {producto.nombre} ({talle.nombre})")
            
            # Usar precio actual (con descuento de producto si existe, e.g. oferta base)
            precio_unitario = producto.get_precio_actual()
            subtotal_item = precio_unitario * cantidad
            
            # Chequear Promociones AUTOMÁTICAS (no cupones)
            promo_auto_descuento = 0
            promos_auto = PromocionProducto.query.filter_by(activa=True, es_cupon=False).all()
            for promo in promos_auto:
                if promo.esta_activa() and OrderService._is_promo_applicable(promo, producto):
                    promo_auto_descuento += promo.calcular_descuento(cantidad, precio_unitario)
            
            descuento_promo_automatica_total += promo_auto_descuento
            subtotal_calculado += subtotal_item
            
            items_procesados.append({
                'producto': producto,
                'talle': talle,
                'cantidad': cantidad,
                'precio_unitario': precio_unitario,
                'descuento_aplicado': promo_auto_descuento,
                'subtotal': subtotal_item - promo_auto_descuento
            })

        # Aplicar descuento de promociones automáticas al subtotal base? 
        # Depende de lógica de negocio, asumimos que subtotal es la suma de precios unitarios
        # y el descuento se resta después o se impacta en el total.
        # En el modelo actual: subtotal es valor bruto, descuento es campo separado.
        
        # 2. Crear Pedido Base
        numero_pedido = OrderService._generate_next_order_id()
        pedido = Pedido(
            numero_pedido=numero_pedido,
            cliente_nombre=data.get('cliente_nombre'),
            cliente_email=data.get('cliente_email'),
            cliente_telefono=data.get('cliente_telefono', ''),
            cliente_direccion=data.get('calle', '') + ' ' + str(data.get('altura', '')),
            cliente_codigo_postal=data.get('codigo_postal'),
            cliente_localidad=data.get('ciudad'),
            cliente_provincia=data.get('provincia'),
            cliente_dni=data.get('dni'),
            metodo_pago_id=metodo_pago_id,
            metodo_envio=data.get('metodo_envio', 'correo_argentino'),
            costo_envio=float(data.get('costo_envio', 0)),
            estado='pendiente_aprobacion',
            aprobado=False,
            # Subtotal inicial calculado
            subtotal=subtotal_calculado, 
            descuento=descuento_promo_automatica_total,
            total=0, # Se calcula al final
            fecha_expiracion=datetime.now() + timedelta(days=5)
        )
        
        db.session.add(pedido)
        db.session.flush() # Para tener ID de pedido
        
        # 3. Guardar Items
        for item in items_procesados:
            item_pedido = ItemPedido(
                pedido_id=pedido.id,
                producto_id=item['producto'].id,
                talle_id=item['talle'].id,
                cantidad=item['cantidad'],
                precio_unitario=item['precio_unitario'],
                descuento_aplicado=item['descuento_aplicado'],
                subtotal=item['subtotal']
            )
            db.session.add(item_pedido)
            
        # 4. Procesar Cupón (si existe)
        descuento_cupon = 0
        codigo_cupon = data.get('codigo_cupon')
        if codigo_cupon:
            cupon = PromocionProducto.query.filter_by(codigo=codigo_cupon, activa=True, es_cupon=True).first()
            if not cupon or not cupon.esta_activa():
                raise Exception("Cupón inválido o expirado")
            
            if cupon.max_usos is not None and cupon.usos_actuales >= cupon.max_usos:
                raise Exception("Cupón agotado")
                
            if subtotal_calculado < cupon.compra_minima:
                raise Exception(f"Monto mínimo para este cupón: ${cupon.compra_minima}")
            
            # Aplicar cupón por alcance
            cupon_aplicado_items = False
            
            # Recargar items vinculados para asegurar consistencia
            for item in pedido.items:
                producto = Producto.query.get(item.producto_id) # O usar relación directo si lazy load
                if OrderService._is_promo_applicable(cupon, producto):
                    desc = cupon.calcular_descuento(item.cantidad, item.precio_unitario)
                    item.descuento_aplicado += desc
                    item.subtotal -= desc
                    descuento_cupon += desc
                    cupon_aplicado_items = True

            # Si es envío gratis
            if cupon.envio_gratis:
                pedido.costo_envio = 0
                descuento_cupon += float(data.get('costo_envio', 0)) # Contabilizar como descuento visualmente si se quiere

            if descuento_cupon > 0 or cupon.envio_gratis:
                cupon.usos_actuales += 1
            else:
                 # Si no aplicó a nada
                pass
        
        pedido.descuento += descuento_cupon

        # 5. Aplicar descuento del 15% por Método de Pago (Transferencia o Efectivo Local o Efectivo Rapipago)
        # El usuario pidió explícitamente que Rapipago/PagoFacil tenga el descuento
        descuento_pago = 0
        metodo = MetodoPago.query.get(metodo_pago_id)
        # Validar keywords: 'transferencia', 'efectivo' (que cubre efectivo local y efectivo rapipago)
        if metodo:
            nombre_metodo = metodo.nombre.lower()
            if 'transferencia' in nombre_metodo or 'efectivo' in nombre_metodo:
                # El descuento aplica sobre (Subtotal - DescuentosPrevios + Envio) o directo?
                # Generalmente es sobre el total final a pagar.
                base_calculo = (pedido.subtotal - pedido.descuento) + pedido.costo_envio
                # Evitar negativos
                base_calculo = max(0, base_calculo)
                descuento_pago = base_calculo * 0.15
            
        pedido.descuento += descuento_pago
        
        # 6. Calcular Total Final
        # Total = Subtotal + Envio - Descuentos Totales
        # (Ya hemos sumado los descuentos en pedido.descuento)
        total_final = (pedido.subtotal + pedido.costo_envio) - pedido.descuento
        pedido.total = max(0, total_final)
        
        return pedido

    @staticmethod
    def _is_promo_applicable(promo, producto):
        if promo.alcance == 'tienda': return True
        if promo.alcance == 'producto' and any(p.id == producto.id for p in promo.productos): return True
        if promo.alcance == 'categoria' and any(c.id == producto.categoria_id for c in promo.categorias): return True
        return False

    @staticmethod
    def _generate_next_order_id():
        # Obtener el último pedido para calcular la secuencia
        # Filtramos para asegurarnos que tenga el formato correcto (6 caracteres) si hay viejos
        try:
            # Buscar el último pedido creado
            last_order = Pedido.query.order_by(Pedido.id.desc()).first()
            
            if not last_order or not last_order.numero_pedido:
                return 'AA0001'
            
            last_code = last_order.numero_pedido
            
            # Si tiene formato UUID viejo (8 chars o más), ignoramos y empezamos de nuevo?
            # O tratamos de buscar el último con formato válido.
            if len(last_code) != 6 or not last_code[:2].isalpha() or not last_code[2:].isdigit():
                # Fallback: buscar si existe ALGUNO con formato válido para continuar la serie
                # Si es muy costoso, simplemente empezamos en AA0001 y asumimos que es el primero del nuevo sistema.
                return 'AA0001'

            letters = last_code[:2]
            number = int(last_code[2:])
            
            number += 1
            if number > 9999:
                number = 0
                # Incrementar letras
                first_char = letters[0]
                second_char = letters[1]
                
                if second_char == 'Z':
                    second_char = 'A'
                    if first_char == 'Z':
                        # Overflow total (ZZ9999 -> ???) - Reiniciar o error?
                        # Para este caso practico, reiniciamos a AA o extendemos.
                        return 'AAA001' # Edge case improbable corto plazo
                    else:
                        first_char = chr(ord(first_char) + 1)
                else:
                    second_char = chr(ord(second_char) + 1)
                    
                letters = f"{first_char}{second_char}"
            
            return f"{letters}{number:04d}"
            
        except Exception as e:
            print(f"Error generando ID pedido: {e}")
            return 'AA0001'
