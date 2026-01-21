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
    def get_sales_stats(periodo: str, ahora: datetime = None, semana_offset: int = 0, anio: int = None):
        """
        Genera datos para los gráficos de ventas con las nuevas reglas:
        - Semana: 8 semanas desde el 1 de enero del año, navegable por bloques de 8
        - Mes: 12 meses del año especificado, navegable por año
        - Año: Solo el año actual
        """
        if not ahora: ahora = datetime.utcnow()
        datos = []
        intervalos = []
        
        if periodo == 'dia':
            # Día a día: Semana actual (Dom a Sáb) - mantener como estaba
            dia_semana_custom = (ahora.weekday() + 1) % 7
            fecha_domingo = ahora - timedelta(days=dia_semana_custom)
            dias_labels = ['Dom', 'Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb']
            for i in range(7):
                fecha = fecha_domingo + timedelta(days=i)
                inicio = datetime(fecha.year, fecha.month, fecha.day, 0, 0, 0)
                fin = datetime(fecha.year, fecha.month, fecha.day, 23, 59, 59)
                intervalos.append((f"{dias_labels[i]} {fecha.strftime('%d/%m')}", inicio, fin))
        
        elif periodo == 'semana':
            # Semana a semana: 8 semanas desde el 1 de enero del año
            # semana_offset indica cuántos bloques de 8 semanas retroceder
            year = anio if anio else ahora.year
            inicio_ano = datetime(year, 1, 1, 0, 0, 0)
            
            # Calcular la semana de inicio basándose en el offset
            semana_inicio = semana_offset * 8
            fecha_inicio_bloque = inicio_ano + timedelta(weeks=semana_inicio)
            
            # Generar 8 semanas consecutivas
            for i in range(8):
                inicio_semana = fecha_inicio_bloque + timedelta(weeks=i)
                # Ajustar al lunes de esa semana
                dias_hasta_lunes = (inicio_semana.weekday()) % 7
                if dias_hasta_lunes > 0:
                    inicio_semana = inicio_semana - timedelta(days=dias_hasta_lunes)
                
                inicio = datetime(inicio_semana.year, inicio_semana.month, inicio_semana.day, 0, 0, 0)
                fin = inicio + timedelta(days=6, hours=23, minutes=59, seconds=59)
                
                # No mostrar semanas futuras
                if inicio > ahora:
                    break
                    
                label = f"S {inicio.strftime('%d/%m')}"
                intervalos.append((label, inicio, fin))
                
        elif periodo == 'mes':
            # Mes a mes: 12 meses del año especificado
            year = anio if anio else ahora.year
            meses_es = ['', 'Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
            
            for mes_num in range(1, 13):
                inicio = datetime(year, mes_num, 1, 0, 0, 0)
                
                # Calcular último día del mes
                if mes_num == 12:
                    fin = datetime(year + 1, 1, 1) - timedelta(seconds=1)
                else:
                    fin = datetime(year, mes_num + 1, 1) - timedelta(seconds=1)
                
                # No mostrar meses futuros
                if inicio > ahora:
                    break
                    
                intervalos.append((meses_es[mes_num], inicio, fin))
                
        elif periodo == 'anio':
            # Año a año: Mostrar todos los años desde 2024 hasta el actual
            # En 2026 muestra: 2024, 2025, 2026
            # En 2027 muestra: 2024, 2025, 2026, 2027
            anio_actual = ahora.year
            anio_inicio = 2024  # Primer año del sistema
            
            for year in range(anio_inicio, anio_actual + 1):
                inicio = datetime(year, 1, 1, 0, 0, 0)
                fin = datetime(year, 12, 31, 23, 59, 59)
                
                # Si es el año actual y aún no terminó, cortar hasta hoy
                if year == anio_actual and fin > ahora:
                    fin = ahora
                    
                intervalos.append((str(year), inicio, fin))
        
        # Calcular ventas para cada intervalo
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
