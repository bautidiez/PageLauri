from models import db, Producto, Pedido, Admin, Categoria, StockTalle, VentaExterna
from sqlalchemy import func
from datetime import datetime, timedelta

class AdminService:
    @staticmethod
    def get_dashboard_stats():
        """
        Calcula las estadísticas principales para el dashboard.
        """
        total_productos = Producto.query.count()
        productos_activos = Producto.query.filter_by(activo=True).count()
        
        # Productos sin stock comercializable (<= 5 según lógica de negocio)
        productos_sin_stock = Producto.query.filter(
            ~Producto.stock_talles.any(StockTalle.cantidad > 5)
        ).count()
        
        total_pedidos = Pedido.query.count()
        pedidos_pendientes_aprobacion = Pedido.query.filter_by(aprobado=False, estado='pendiente_aprobacion').count()
        pedidos_pendientes = Pedido.query.filter(Pedido.estado.in_(['pendiente', 'pendiente_aprobacion', 'confirmado'])).count()
        
        # Ventas totales (solo pedidos APROBADOS y entregados)
        total_ventas_web = db.session.query(func.sum(Pedido.total)).filter(
            Pedido.aprobado == True,
            Pedido.estado == 'entregado'
        ).scalar() or 0
        
        # Ventas externas (todas cuentan ya que son confirmadas al momento de registro)
        total_ventas_externas = db.session.query(func.sum(VentaExterna.ganancia_total)).scalar() or 0
        
        # Total combinado
        total_ventas = total_ventas_web + total_ventas_externas
        
        return {
            'productos': {
                'total': total_productos,
                'activos': productos_activos,
                'bajo_stock': productos_sin_stock
            },
            'pedidos': {
                'total': total_pedidos,
                'pendientes': pedidos_pendientes,
                'pendientes_aprobacion': pedidos_pendientes_aprobacion
            },
            'ventas': {
                'total': float(total_ventas)
            }
        }

    @staticmethod
    def get_sales_stats(periodo: str, ahora: datetime = None):
        """
        Genera datos para los gráficos de ventas.
        """
        if not ahora: ahora = datetime.utcnow()
        datos = []
        intervalos = []
        
        if periodo == 'dia':
            # Semana actual (Dom a Sáb)
            dia_semana_custom = (ahora.weekday() + 1) % 7
            fecha_domingo = ahora - timedelta(days=dia_semana_custom)
            dias_labels = ['Dom', 'Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb']
            for i in range(7):
                fecha = fecha_domingo + timedelta(days=i)
                inicio = datetime(fecha.year, fecha.month, fecha.day, 0, 0, 0)
                fin = datetime(fecha.year, fecha.month, fecha.day, 23, 59, 59)
                intervalos.append((f"{dias_labels[i]} {fecha.strftime('%d/%m')}", inicio, fin))
        
        # ... (Agregar lógica de semana/mes/año si es necesario moverla toda)
        
        max_venta = 0
        total_periodo = 0
        for label, inicio, fin in intervalos:
            # Ventas del sitio web
            ventas_web = db.session.query(func.sum(Pedido.total)).filter(
                Pedido.aprobado == True,
                Pedido.estado == 'entregado',
                Pedido.created_at.between(inicio, fin)
            ).scalar() or 0
            
            # Ventas externas
            ventas_externas = db.session.query(func.sum(VentaExterna.ganancia_total)).filter(
                VentaExterna.fecha.between(inicio, fin)
            ).scalar() or 0
            
            # Total combinado
            ventas = ventas_web + ventas_externas
            datos.append({'label': label, 'ventas': float(ventas), 'fecha': inicio.isoformat()})
            max_venta = max(max_venta, ventas)
            total_periodo += ventas
            
        return {
            'periodo': periodo,
            'datos': datos,
            'total_periodo': float(total_periodo),
            'max_venta': float(max_venta) if max_venta > 0 else 1
        }
