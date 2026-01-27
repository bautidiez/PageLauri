
from app import create_app, db
from models import MetodoPago

app = create_app()

def force_populate_methods():
    with app.app_context():
        print("Starting Payment Method Population...")
        
        # Define desired methods with precise names matched by frontend/backend logic
        methods = [
            {'id': 1, 'nombre': 'transferencia', 'descripcion': 'Transferencia Bancaria'},
            {'id': 2, 'nombre': 'efectivo', 'descripcion': 'Efectivo (Rapipago/Pago Fácil)'}, # ID might vary if auto-incremented, but name is key
            {'id': 3, 'nombre': 'tarjeta_credito', 'descripcion': 'Tarjeta de Crédito'},
            {'id': 4, 'nombre': 'tarjeta_debito', 'descripcion': 'Tarjeta de Débito'},
            # Custom ones mapping to frontend keys
            {'nombre': 'efectivo_local', 'descripcion': 'Efectivo en el Local', 'activo': True},
            {'nombre': 'mercadopago', 'descripcion': 'Mercado Pago / Tarjeta', 'activo': True}
        ]
        
        for m_data in methods:
            # Check by name first
            existing = MetodoPago.query.filter(MetodoPago.nombre.ilike(m_data['nombre'])).first()
            
            if not existing:
                print(f"Creating missing method: {m_data['nombre']}")
                new_method = MetodoPago(
                    nombre=m_data['nombre'],
                    descripcion=m_data['descripcion'],
                    activo=m_data.get('activo', True)
                )
                db.session.add(new_method)
            else:
                print(f"Method already exists: {existing.nombre} (ID: {existing.id})")
                
                # Force ID check if specific ID was requested? No, IDs are immutable typically.
                # But we can verify it's active
                if not existing.activo:
                    existing.activo = True
                    print(f"  -> Reactivated {existing.nombre}")

        db.session.commit()
        print("Population Complete.")

if __name__ == "__main__":
    force_populate_methods()
