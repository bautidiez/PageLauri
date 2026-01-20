from flask import Blueprint, request, jsonify
import time
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from models import Admin
from extensions import limiter

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/api/auth/login', methods=['POST'])
@limiter.limit("5 per minute")
def login():
    """Login de administrador"""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': 'Usuario y contraseña requeridos'}), 400
    
    print(f"DEBUG LOGIN ADMIN: Password recibido: '{password}' (len={len(password)})")
    # Log the first 2 and last 2 chars to check for weird encoding/chars without exposing full pass
    if len(password) > 4:
        print(f"DEBUG LOGIN ADMIN: Peek password: {password[:2]}...{password[-2:]}")
    
    admin = Admin.query.filter_by(username=username).first()
    
    if not admin:
        print(f"DEBUG LOGIN ADMIN: Usuario '{username}' no encontrado en la base de datos.")
        return jsonify({'error': 'Usuario no encontrado'}), 401
    
    print(f"DEBUG LOGIN ADMIN: Hash en BD: {admin.password_hash}")
    
    # Pruebas de hashing locales para comparar
    from werkzeug.security import generate_password_hash, check_password_hash
    test_hash = generate_password_hash(password)
    test_verify = check_password_hash(test_hash, password)
    print(f"DEBUG LOGIN ADMIN: Test validacion local con mismo pass: {test_verify}")
    print(f"DEBUG LOGIN ADMIN: Test hash local: {test_hash[:50]}...")

    start_hash = time.time()
    is_valid = admin.check_password(password)
    hash_time = (time.time() - start_hash) * 1000
    
    print(f"DEBUG LOGIN ADMIN: Validacion contra BD: {is_valid} (tomó {hash_time:.1f}ms)")
    
    if is_valid:
        access_token = create_access_token(identity=str(admin.id))
        return jsonify({
            'access_token': access_token,
            'admin': admin.to_dict()
        }), 200
    
    print(f"DEBUG LOGIN ADMIN: Contraseña incorrecta para el usuario: {username}")
    return jsonify({'error': 'Contraseña incorrecta'}), 401

@auth_bp.route('/api/auth/verify', methods=['GET'])
@jwt_required()
def verify_token():
    """Verificar token JWT - OPTIMIZADO (sin consulta a BD)"""
    admin_id = get_jwt_identity()
    # NO consultar la BD - solo verificar que el token sea válido
    return jsonify({
        'admin': {
            'id': int(admin_id),
            'authenticated': True
        }
    }), 200

@auth_bp.route('/api/auth/emergency-reset-admin', methods=['POST'])
def emergency_reset_admin():
    """ENDPOINT TEMPORAL: Resetear password del admin (BORRAR DESPUÉS)"""
    import os
    from werkzeug.security import generate_password_hash
    from models import db, Admin
    
    data = request.get_json()
    secret = data.get('secret')
    
    # Verificar que tiene la clave secreta correcta
    if secret != os.environ.get('SECRET_KEY'):
        return jsonify({'error': 'No autorizado'}), 403
    
    try:
        admin = Admin.query.filter_by(username='admin').first()
        raw_password = os.environ.get('ADMIN_INITIAL_PASSWORD', 'ElVestuario2024!Admin')
        new_password = raw_password.strip()
        
        if not admin:
            return jsonify({'error': 'Admin no encontrado'}), 404
        
        print(f"DEBUG EMERGENCY RESET: Generando hash para password largo {len(new_password)}")
        print(f"DEBUG EMERGENCY RESET: Peek: {new_password[:2]}...{new_password[-2:]}")
        
        from werkzeug.security import generate_password_hash, check_password_hash
        new_hash = generate_password_hash(new_password)
        print(f"DEBUG EMERGENCY RESET: Nuevo hash generado: {new_hash[:50]}...")
        
        # Verificar inmediatamente
        is_instantly_valid = check_password_hash(new_hash, new_password)
        print(f"DEBUG EMERGENCY RESET: Verificacion inmediata del nuevo hash: {is_instantly_valid}")
        
        admin.password_hash = new_hash
        db.session.commit()
        
        print(f"✓ EMERGENCY RESET: Password actualizado para admin")
        return jsonify({
            'success': True,
            'message': 'Password reseteado exitosamente',
            'username': 'admin',
            'debug_len': len(new_password),
            'instant_check': is_instantly_valid
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
