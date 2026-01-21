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
        
        # Ventas totales (Pedidos APROBADOS que no estén cancelados/fallidos)
        total_ventas_web = db.session.query(func.sum(Pedido.total)).filter(
            Pedido.aprobado == True,
            Pedido.estado.in_(['confirmado', 'enviado', 'entregado'])
        ).scalar() or 0
        
        # Ventas externas (todas cuentan)
        total_ventas_externas = db.session.query(func.sum(VentaExterna.ganancia_total)).scalar() or 0
        
        # Total combinado
        total_ventas = float(total_ventas_web) + float(total_ventas_externas)
        
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
        
        elif periodo == 'semana':
            # Últimas 8 semanas
            for i in range(7, -1, -1):
                inicio_semana = ahora - timedelta(weeks=i)
                inicio_semana = inicio_semana - timedelta(days=(inicio_semana.weekday() + 1) % 7)
                inicio = datetime(inicio_semana.year, inicio_semana.month, inicio_semana.day, 0, 0, 0)
                fin = inicio + timedelta(days=6, hours=23, minutes=59, seconds=59)
                label = f"S {inicio.strftime('%d/%m')}"
                intervalos.append((label, inicio, fin))
                
        elif periodo == 'mes':
            # Últimos 6 meses
            for i in range(5, -1, -1):
                mes = (ahora.month - 1 - i) % 12 + 1
                anio = ahora.year + (ahora.month - 1 - i) // 12
                inicio = datetime(anio, mes, 1, 0, 0, 0)
                # Siguiente mes - 1 día
                if mes == 12:
                    fin = datetime(anio + 1, 1, 1) - timedelta(seconds=1)
                else:
                    fin = datetime(anio, mes + 1, 1) - timedelta(seconds=1)
                
                meses_es = ['', 'Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
                intervalos.append((meses_es[mes], inicio, fin))
                
        elif periodo == 'anio':
            # Últimos 3 años (o más si es necesario)
            anio_actual = ahora.year
            for i in range(2, -1, -1):
                anio = anio_actual - i
                inicio = datetime(anio, 1, 1, 0, 0, 0)
                fin = datetime(anio, 12, 31, 23, 59, 59)
                intervalos.append((str(anio), inicio, fin))
        
        max_venta = 0
        total_periodo = 0
        for label, inicio, fin in intervalos:
            # Ventas del sitio web (Aprobados o Entregados)
            ventas_web = db.session.query(func.sum(Pedido.total)).filter(
                Pedido.aprobado == True,
                Pedido.estado.in_(['confirmado', 'enviado', 'entregado']),
                Pedido.created_at.between(inicio, fin)
            ).scalar() or 0
            
            # Ventas externas
            ventas_externas = db.session.query(func.sum(VentaExterna.ganancia_total)).filter(
                VentaExterna.fecha.between(inicio, fin)
            ).scalar() or 0
            
            # Total combinado
            ventas = float(ventas_web) + float(ventas_externas)
            datos.append({'label': label, 'ventas': ventas, 'fecha': inicio.isoformat()})
            max_venta = max(max_venta, ventas)
            total_periodo += ventas
            
        return {
            'periodo': periodo,
            'datos': datos,
            'total_periodo': float(total_periodo),
            'max_venta': float(max_venta) if max_venta > 0 else 1
        }
