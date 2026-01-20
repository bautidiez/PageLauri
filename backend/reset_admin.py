import os
import secrets
from app import app
from models import db, Admin
from werkzeug.security import generate_password_hash

def reset_admin():
    with app.app_context():
        admin = Admin.query.filter_by(username='admin').first()
        new_pass = os.environ.get('ADMIN_INITIAL_PASSWORD', 'ElVestuario2024!Admin')
        
        if admin:
            admin.password_hash = generate_password_hash(new_pass)
            print(f"✅ Password del usuario 'admin' actualizado a: {new_pass}")
        else:
            admin = Admin(
                username='admin',
                email='admin@elvestuario.com',
                password_hash=generate_password_hash(new_pass)
            )
            db.session.add(admin)
            print(f"✅ Usuario 'admin' creado con contraseña: {new_pass}")
        
        db.session.commit()
        print("🚀 Cambios guardados en la base de datos.")

if __name__ == "__main__":
    reset_admin()
