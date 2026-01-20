"""
Script para verificar ofertas
"""
from app import app, db
from models import Producto, PromocionProducto
from datetime import datetime

with app.app_context():
    ahora = datetime.utcnow()
    
    # Productos con precio_descuento
    prod_desc = Producto.query.filter(
        Producto.precio_descuento.isnot(None),
        Producto.precio_descuento > 0,
        Producto.activo == True
    ).count()
    print(f'✓ Productos con precio_descuento: {prod_desc}')
    
    # Promociones activas
    promos_activas = PromocionProducto.query.filter(
        PromocionProducto.activa == True,
        PromocionProducto.fecha_inicio <= ahora,
        PromocionProducto.fecha_fin >= ahora
    ).all()
    print(f'✓ Promociones activas totales: {len(promos_activas)}')
    
    for promo in promos_activas:
        print(f'  - Promo ID {promo.id}: {promo.alcance}')
        print(f'    Productos directos: {len(promo.productos)}')
        print(f'    Categorías: {len(promo.categorias)}')
