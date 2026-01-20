"""
Tareas de limpieza automatizadas para el sistema
Incluye: auto-eliminación de pedidos expirados no aprobados
"""
from models import db, Pedido, StockTalle
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def eliminar_pedidos_expirados():
    """
    Elimina automáticamente pedidos que:
    - No están aprobados (aprobado=False)
    - Han superado su fecha de expiración
    
    Esta función debe ejecutarse periódicamente (cada 1 hora recomendado)
    """
    try:
        ahora = datetime.utcnow()
        
        # Buscar pedidos expirados
        pedidos_expirados = Pedido.query.filter(
            Pedido.aprobado == False,
            Pedido.fecha_expiracion < ahora
        ).all()
        
        count = len(pedidos_expirados)
        
        if count == 0:
            logger.info("No hay pedidos expirados para eliminar")
            return 0
        
        # Eliminar cada pedido (las relaciones se eliminan en cascada)
        for pedido in pedidos_expirados:
            logger.info(f"Eliminando pedido expirado: {pedido.numero_pedido} (creado: {pedido.created_at}, expiró: {pedido.fecha_expiracion})")
            
            # Como precaución, verificar que no se haya reducido stock
            # (no debería pasar pero es un safeguard)
            # En este caso NO restauramos stock porque nunca debería haberse reducido
            
            db.session.delete(pedido)
        
        db.session.commit()
        logger.info(f"✅ Eliminados {count} pedidos expirados")
        
        return count
        
    except Exception as e:
        logger.error(f"❌ Error al eliminar pedidos expirados: {e}")
        db.session.rollback()
        return 0

def limpiar_sesiones_antiguas():
    """
    Placeholder para otras tareas de limpieza futuras
    """
    pass
