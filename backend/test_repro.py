from app import app, db
from models import Producto, StockTalle, Talle, MetodoPago
from services.order_service import OrderService
import sys
import traceback


def run_test():
    with open("repro_output.txt", "w", encoding="utf-8") as f:
        try:
            with app.app_context():
                # 1. Use verified products
                short = Producto.query.get(62)
                short_talle = Talle.query.get(2)
                
                other = Producto.query.get(5)
                other_talle = Talle.query.get(6)

                if not short or not other:
                    f.write("Could not find suitable products for test.\n")
                    return

                # 2. Setup Mock Payment Methods
                pm_efectivo = MetodoPago.query.filter_by(nombre="Efectivo Test").first()
                if not pm_efectivo:
                    pm_efectivo = MetodoPago(nombre="Efectivo Test", activo=True)
                    db.session.add(pm_efectivo)
                
                pm_tarjeta = MetodoPago.query.filter_by(nombre="Tarjeta Test").first()
                if not pm_tarjeta:
                    pm_tarjeta = MetodoPago(nombre="Tarjeta Test", activo=True)
                    db.session.add(pm_tarjeta)
                    
                db.session.commit() # Commit to get IDs and be visible

                f.write(f"Test Products: Short={short.id} (${short.precio_base}), Other={other.id} (${other.precio_base})\n")
                f.write(f"PM Efectivo: {pm_efectivo.id}, PM Tarjeta: {pm_tarjeta.id}\n")

                # Mock Data Helper
                def create_payload(items, metodo_pago_id):
                    return {
                        "cliente_nombre": "Test User",
                        "cliente_email": "test@example.com",
                        "metodo_pago_id": metodo_pago_id,
                        "metodo_envio": "retiro_local",
                        "items": items,
                        "codigo_postal": "1234",
                        "calle": "Calle Falsa",
                        "altura": 123,
                        "ciudad": "Springfield",
                        "provincia": "Buenos Aires",
                        "dni": "12345678"
                    }

                f.write("\n--- TEST CASE 1: 1 Short (Cash) ---\n")
                # Current: 15% Payment Discount
                # Expected New: 10% Payment Discount
                payload = create_payload([
                    {"producto_id": short.id, "talle_id": short_talle.id, "cantidad": 1}
                ], metodo_pago_id=pm_efectivo.id)
                order = OrderService.create_order(payload)
                
                f.write(f"Subtotal: {order.subtotal}\n")
                f.write(f"Descuento Total: {order.descuento}\n")
                f.write(f"Total: {order.total}\n")
                payment_percentage = (order.descuento / order.subtotal) * 100
                f.write(f"Effective Discount %: {payment_percentage:.2f}%\n")

                f.write("\n--- TEST CASE 2: 2 items (Shorts) (Mix) ---\n")
                # New: 10% Qty Discount
                payload = create_payload([
                    {"producto_id": short.id, "talle_id": short_talle.id, "cantidad": 2}
                ], metodo_pago_id=pm_tarjeta.id) # Card
                
                try:
                    order = OrderService.create_order(payload)
                    f.write(f"Subtotal: {order.subtotal}\n")
                    f.write(f"Descuento Total: {order.descuento}\n")
                    f.write(f"Total: {order.total}\n")
                    qty_percentage = (order.descuento / order.subtotal) * 100 if order.subtotal > 0 else 0
                    f.write(f"Effective Discount %: {qty_percentage:.2f}%\n")
                except Exception as e:
                    f.write(f"Error in Case 2: {e}\n")
                    f.write(traceback.format_exc())

                f.write("\n--- TEST CASE 3: 3 items (Shorts) (Mix) ---\n")
                # New: 15% Qty Discount
                payload = create_payload([
                    {"producto_id": short.id, "talle_id": short_talle.id, "cantidad": 3}
                ], metodo_pago_id=pm_tarjeta.id)
                
                try:
                    order = OrderService.create_order(payload)
                    f.write(f"Subtotal: {order.subtotal}\n")
                    f.write(f"Descuento Total: {order.descuento}\n")
                    qty_percentage = (order.descuento / order.subtotal) * 100 if order.subtotal > 0 else 0
                    f.write(f"Effective Discount %: {qty_percentage:.2f}%\n")
                except Exception as e:
                     f.write(f"Error in Case 3: {e}\n")
                     f.write(traceback.format_exc())

                f.write("\n--- TEST CASE 4: 1 Remera (Cash) ---\n")
                # Expected: 15% Payment Discount (Status Quo)
                payload = create_payload([
                    {"producto_id": other.id, "talle_id": other_talle.id, "cantidad": 1}
                ], metodo_pago_id=pm_efectivo.id)
                order = OrderService.create_order(payload)
                f.write(f"Subtotal: {order.subtotal}\n")
                f.write(f"Descuento Total: {order.descuento}\n")
                payment_percentage = (order.descuento / order.subtotal) * 100 if order.subtotal > 0 else 0
                f.write(f"Effective Discount %: {payment_percentage:.2f}%\n")

                db.session.rollback() # Don't save test orders
        except Exception:
            f.write("FATAL ERROR:\n")
            f.write(traceback.format_exc())



run_test()
