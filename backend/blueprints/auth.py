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
    
    start_time = time.time()
    admin = Admin.query.filter_by(username=username).first()
    query_time = (time.time() - start_time) * 1000
    
    start_hash = time.time()
    is_valid = admin and admin.check_password(password)
    hash_time = (time.time() - start_hash) * 1000
    
    print(f"DEBUG LOGIN ADMIN: Query {query_time:.1f}ms, Hashing {hash_time:.1f}ms")
    
    if is_valid:
        access_token = create_access_token(identity=str(admin.id))
        return jsonify({
            'access_token': access_token,
            'admin': admin.to_dict()
        }), 200
    
    return jsonify({'error': 'Credenciales inválidas'}), 401

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
