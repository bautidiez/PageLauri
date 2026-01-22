from app import app, db
from models import PromocionProducto, TipoPromocion
from datetime import datetime, timedelta

with app.app_context():
    try:
        print("Intentando crear promoción de prueba...")
        tipo = TipoPromocion.query.first()
        if not tipo:
            print("ERROR: No hay tipos de promoción.")
            exit(1)
            
        data = {
            'alcance': 'tienda',
            'tipo_promocion_id': tipo.id,
            'valor': 10.0,
            'activa': True,
            'fecha_inicio': datetime.utcnow().isoformat() + 'Z',
            'fecha_fin': (datetime.utcnow() + timedelta(days=30)).isoformat() + 'Z',
            'es_cupon': False,
            'codigo': None,
            'envio_gratis': False,
            'compra_minima': 0
        }
        
        promocion = PromocionProducto(
            alcance=data.get('alcance', 'producto'),
            tipo_promocion_id=data['tipo_promocion_id'],
            valor=float(data.get('valor', 0)),
            activa=data.get('activa', True),
            fecha_inicio=datetime.fromisoformat(data['fecha_inicio'].replace('Z', '+00:00')),
            fecha_fin=datetime.fromisoformat(data['fecha_fin'].replace('Z', '+00:00')),
            es_cupon=data.get('es_cupon', False),
            codigo=data.get('codigo'),
            envio_gratis=data.get('envio_gratis', False),
            compra_minima=float(data.get('compra_minima', 0))
        )
        
        db.session.add(promocion)
        db.session.commit()
        print(f"✓ Promoción de prueba creada con ID: {promocion.id}")
        
        # Limpiar la de prueba
        db.session.delete(promocion)
        db.session.commit()
        print("✓ Promoción de prueba eliminada para dejar limpia la BD.")
        
    except Exception as e:
        print(f"❌ ERROR al crear promoción: {str(e)}")
        import traceback
        traceback.print_exc()
