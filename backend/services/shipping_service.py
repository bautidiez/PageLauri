from .shipping_providers import AndreaniProvider, CorreoArgentinoProvider
import logging

logger = logging.getLogger(__name__)

class ShippingService:
    @staticmethod
    def calculate_cost(zip_code, items=None):
        """
        Lógica completa de cotización desde Río Cuarto (CP 5800).
        """
        try:
            zip_code_val = int(zip_code)
        except (ValueError, TypeError):
            logger.error(f"ZIP code inválido: {zip_code}")
            return []

        # 1. Calcular peso y dimensiones agregadas
        total_weight = 0
        max_length = 0
        max_width = 0
        total_height = 0
        
        if not items:
            # Fallback a un bulto standard si no hay items definidos
            total_weight = 0.5
            dimensions = {"length": 30, "width": 20, "height": 5}
        else:
            for item in items:
                nombre = item.get('producto', {}).get('nombre', '').lower()
                cantidad = item.get('cantidad', 1)
                
                # Criterio según requerimiento
                if 'remera' in nombre:
                    w = 0.30
                    l, wd, h = 30, 20, 2 # cm
                elif 'short' in nombre:
                    w = 0.20
                    l, wd, h = 25, 15, 2
                else:
                    w = 0.25
                    l, wd, h = 25, 20, 2
                
                total_weight += (w * cantidad)
                max_length = max(max_length, l)
                max_width = max(max_width, wd)
                total_height += (h * cantidad)
            
            # Margen mínimo de empaque
            total_height = max(total_height, 2)
            dimensions = {
                "length": max_length,
                "width": max_width,
                "height": total_height
            }

        # 2. Lógica de Envío Gratis
        total_cart_value = 0
        all_items_free_shipping = True
        
        # Necesitamos importar los modelos aquí para evitar ciclos
        from models import Producto

        # Analizar items para calcular total y verificar banderas de envío gratis
        if items:
            for item in items:
                try:
                    # Robust ID extraction
                    p_id = None
                    if 'producto_id' in item:
                        p_id = item['producto_id']
                    elif 'producto' in item:
                        prod_data = item['producto']
                        if isinstance(prod_data, dict):
                            p_id = prod_data.get('id')
                        else:
                            p_id = prod_data # Assume it's the ID itself if not dict
                    
                    qty = int(item.get('cantidad', 1))
                    
                    if not p_id:
                        logger.warning(f"Skipping item with no ID: {item}")
                        continue
                    
                    # Ensure ID is int
                    try:
                        p_id = int(p_id)
                    except:
                        pass

                    # Buscar producto real en DB para precio y promos
                    prod_db = Producto.query.get(p_id)
                    if prod_db:
                        # Use precio_base explicitly for Free Shipping threshold as per user request
                        # (Ignore specific product discounts or payment method discounts)
                        price = prod_db.precio_base
                        item_total = price * qty
                        total_cart_value += item_total
                        print(f"DEBUG SHIPPING: Item {p_id} Base Price ${price} x {qty} = ${item_total} (Subtotal: {total_cart_value})", flush=True)
                        
                        # Verificar si tiene promo de envío gratis activa
                        promos = prod_db.get_promociones_activas()
                        has_free = any(p.envio_gratis for p in promos)
                        if not has_free:
                            all_items_free_shipping = False
                    else:
                        # Si no se encuentra producto, asumir que no es gratis
                        logger.warning(f"Product not found in DB: {p_id}")
                        all_items_free_shipping = False
                except Exception as e:
                    logger.error(f"Error checking free shipping for item: {e}")
                    all_items_free_shipping = False
        
        print(f"DEBUG SHIPPING: Final Total Value {total_cart_value}, All Free? {all_items_free_shipping}", flush=True)

        # Regla: Gratis si Supera $150.000 O si TODOS los productos tienen envío gratis
        is_free_shipping = False
        if total_cart_value >= 150000:
            is_free_shipping = True
            print(f"DEBUG SHIPPING: FREE by VALUE ({total_cart_value} >= 150000)", flush=True)
        elif items and all_items_free_shipping:
            is_free_shipping = True
            print(f"DEBUG SHIPPING: FREE by PROMO (All items free)", flush=True)
        else:
            print(f"DEBUG SHIPPING: PAID (Total {total_cart_value} <= 150000 and not all free)", flush=True)

        results = []
        
        # 3. Consultar proveedores
        providers = [
            AndreaniProvider(),
            CorreoArgentinoProvider()
        ]
        
        for provider in providers:
            try:
                rates = provider.calculate_rates(zip_code_val, weight=total_weight, dimensions=dimensions)
                
                # APLICAR GRATUIDAD
                if is_free_shipping:
                    for r in rates:
                        r['descuento'] = r['costo']  # Guardamos el descuento
                        r['costo_original'] = r['costo'] # Opcional, para referencia
                        # NO ponemos costo a 0 aquí, lo manejamos en el frontend o enviamos costo 0 pero con flag?
                        # User wants: "Show discount of shipping and discount the value".
                        # If we send cost > 0, frontend adds it.
                        # So we send cost > 0 AND discount > 0.
                        r['nombre'] = f"{r['nombre']} (¡Envío Gratis!)" # Mantenemos etiqueta
                
                results.extend(rates)
            except Exception as e:
                logger.error(f"Error en provider {type(provider).__name__}: {str(e)}")

        # 4. Fallbacks (si las APIs fallan o no están configuradas)
        has_andreani = any('andreani' in opt['id'] for opt in results)
        
        if not has_andreani:
            # Send FULL cost here, discount applied later if needed
            cost_sucursal = 5200 if zip_code_val < 3000 else 6800
            cost_domicilio = 6200 if zip_code_val < 3000 else 7900
            
            res_suc = {
                "id": "andreani_sucursal_fallback",
                "nombre": "Andreani (Retiro en Sucursal)",
                "costo": cost_sucursal,
                "tiempo_estimado": "2 a 4 días hábiles"
            }
            res_dom = {
                "id": "andreani_domicilio_fallback",
                "nombre": "Andreani (Envío a Domicilio)",
                "costo": cost_domicilio,
                "tiempo_estimado": "3 a 5 días hábiles"
            }

            if is_free_shipping:
                res_suc['descuento'] = cost_sucursal
                res_suc['nombre'] += " (¡Envío Gratis!)"
                res_dom['descuento'] = cost_domicilio
                res_dom['nombre'] += " (¡Envío Gratis!)"

            results.append(res_suc)
            results.append(res_dom)

        # 5. Opción de Retiro en local (Río Cuarto)
        results.append({
            "id": "retiro_local",
            "nombre": "Retiro en Local (Río Cuarto)",
            "costo": 0,
            "tiempo_estimado": "Inmediato - Te avisaremos por WhatsApp"
        })
        
        # 6. Ordenar y devolver
        return sorted(results, key=lambda x: x['costo'])
