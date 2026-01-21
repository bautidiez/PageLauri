from flask import Blueprint, request, jsonify
import time
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from models import Admin, db
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
    
    admin = Admin.query.filter(db.func.lower(Admin.username) == db.func.lower(username)).first()
    
    if not admin:
        return jsonify({'error': 'Usuario no encontrado'}), 401
    
    if admin.check_password(password):
        access_token = create_access_token(identity=str(admin.id))
        return jsonify({
            'access_token': access_token,
            'admin': admin.to_dict()
        }), 200
    
    return jsonify({'error': 'Contraseña incorrecta'}), 401

@auth_bp.route('/api/auth/login-unified', methods=['POST'])
@limiter.limit("10 per minute")
def login_unified():
    """Login unificado para Admin y Cliente"""
    data = request.get_json()
    # Soporta 'identifier' (nuevo), o 'username'/'email' (compatibilidad)
    identifier = data.get('identifier') or data.get('username') or data.get('email')
    password = data.get('password')
    
    if not identifier or not password:
        return jsonify({'error': 'Credenciales requeridas'}), 400
    
    # 1. Intentar como Admin (por username o email, insensible a mayúsculas)
    admin = Admin.query.filter(
        (db.func.lower(Admin.username) == db.func.lower(identifier)) | 
        (db.func.lower(Admin.email) == db.func.lower(identifier))
    ).first()
    
    if admin and admin.check_password(password):
        access_token = create_access_token(identity=str(admin.id))
        return jsonify({
            'access_token': access_token,
            'user_type': 'admin',
            'admin': admin.to_dict()
        }), 200
        
    from models import Cliente
    cliente = Cliente.query.filter(db.func.lower(Cliente.email) == db.func.lower(identifier)).first()
    if cliente and cliente.check_password(password):
        if not cliente.telefono_verificado:
            return jsonify({
                'error': 'Requiere verificación', 
                'requires_verification': True, 
                'email': cliente.email
            }), 403
            
        access_token = create_access_token(identity=str(cliente.id))
        return jsonify({
            'access_token': access_token,
            'user_type': 'cliente',
            'cliente': cliente.to_dict()
        }), 200
        
    return jsonify({'error': 'Credenciales incorrectas'}), 401

@auth_bp.route('/api/auth/verify', methods=['GET'])
@jwt_required()
def verify_token():
    """Verificar token JWT - OPTIMIZADO (sin consulta a BD)"""
    admin_id = get_jwt_identity()
    return jsonify({
        'admin': {
            'id': int(admin_id),
            'authenticated': True
        }
    }), 200
