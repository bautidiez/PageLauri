from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, create_access_token, get_jwt_identity, decode_token
from extensions import limiter
from models import Cliente, Pedido, db
from services.notification_service import NotificationService
import re
import logging
import random
import time
from datetime import timedelta

logger = logging.getLogger(__name__)
clients_bp = Blueprint('clients', __name__)

@clients_bp.route('/api/clientes', methods=['POST'])
@limiter.limit("50 per hour")
def registrar_cliente():
    try:
        data = request.json
        print(f"DEBUG CLIENTES: Recibida solicitud de registro para {data.get('email')}", flush=True)
        
        if not data.get('nombre') or not data.get('email') or not data.get('password') or not data.get('metodo_verificacion'):
            return jsonify({'error': 'Faltan campos requeridos (incluyendo método de verificación)'}), 400
        
        password = data['password']
        if len(password) < 8 or not re.search(r'[A-Z]', password) or not re.search(r'[a-z]', password) or not re.search(r'\d', password):
            return jsonify({'error': 'La contraseña no cumple los requisitos de seguridad'}), 400
        
        cliente = Cliente.query.filter_by(email=data['email']).first()
        
        if cliente:
            if cliente.telefono_verificado:
                return jsonify({'error': 'Email ya registrado'}), 400
            else:
                # Si existe pero no está verificado, actualizamos sus datos y mandamos código nuevo
                print(f"DEBUG CLIENTES: Re-registro para cuenta no verificada: {data['email']}", flush=True)
                cliente.nombre = data['nombre']
                cliente.telefono = data.get('telefono')
                cliente.metodo_verificacion = 'email'
                cliente.acepta_newsletter = data.get('acepta_newsletter', True)
        else:
            # Crear nuevo cliente
            cliente = Cliente(
                nombre=data['nombre'],
                email=data['email'],
                telefono=data.get('telefono'),
                metodo_verificacion='email',
                acepta_newsletter=data.get('acepta_newsletter', True)
            )
            db.session.add(cliente)
            
        cliente.set_password(password)
        cliente.codigo_verificacion = str(random.randint(100000, 999999))
        db.session.commit()
        
        # Enviar código de forma asíncrona para no demorar la respuesta
        try:
            from threading import Thread
            from flask import current_app
            def send_async_code(app, cliente_id, codigo, metodo):
                with app.app_context():
                    from models import Cliente
                    c = Cliente.query.get(cliente_id)
                    if c:
                        NotificationService.send_verification_code(c, codigo, metodo)

            Thread(target=send_async_code, args=(current_app._get_current_object(), cliente.id, cliente.codigo_verificacion, cliente.metodo_verificacion)).start()
        except Exception as thread_err:
            print(f"DEBUG CLIENTES: Error al lanzar thread de notificación: {thread_err}", flush=True)

        logger.info(f"🆕 REGISTRO OK: {cliente.email} - Verif: {cliente.metodo_verificacion}")
        return jsonify(cliente.to_dict()), 201
        
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"DEBUG CLIENTES: ERROR CRÍTICO en registrar_cliente: {str(e)}\n{error_trace}", flush=True)
        return jsonify({'error': f'Ocurrió un error en el servidor. Por favor intenta más tarde.'}), 500

@clients_bp.route('/api/clientes/login', methods=['POST'])
@limiter.limit("10 per minute")
def login_cliente():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({'error': 'Email y contraseña requeridos'}), 400
    
    cliente = Cliente.query.filter_by(email=email).first()
    if cliente and cliente.check_password(password):
        access_token = create_access_token(identity=str(cliente.id))
        return jsonify({'access_token': access_token, 'cliente': cliente.to_dict()}), 200
    
    return jsonify({'error': 'Credenciales inválidas'}), 401

@clients_bp.route('/api/clientes/verify-code', methods=['POST'])
@limiter.limit("5 per minute")
def verificar_codigo():
    data = request.json
    email = data.get('email')
    codigo_recibido = str(data.get('codigo'))
    
    cliente = Cliente.query.filter_by(email=email).first()
    
    if not cliente:
        print(f"DEBUG VERIFICACION: Email {email} no encontrado", flush=True)
        return jsonify({'error': 'Email no encontrado'}), 404
        
    print(f"DEBUG VERIFICACION: Evaluando {email}. Recibido: [{codigo_recibido}], Esperado: [{cliente.codigo_verificacion}]", flush=True)
    
    if cliente.codigo_verificacion == codigo_recibido:
        cliente.telefono_verificado = True
        cliente.codigo_verificacion = None
        db.session.commit()
        print(f"DEBUG VERIFICACION: {email} verificado con éxito", flush=True)
        
        # Generar token para auto-login
        access_token = create_access_token(identity=str(cliente.id))
        return jsonify({
            'message': 'Verificado',
            'access_token': access_token,
            'cliente': cliente.to_dict()
        }), 200
        
    print(f"DEBUG VERIFICACION: {email} falló. Código incorrecto.", flush=True)
    return jsonify({'error': 'Código inválido'}), 400

@clients_bp.route('/api/clientes/resend-code', methods=['POST'])
@limiter.limit("3 per minute")
def reenviar_codigo():
    data = request.json
    email = data.get('email')
    cliente = Cliente.query.filter_by(email=email).first()
    
    if not cliente:
        return jsonify({'error': 'Email no encontrado'}), 404
    
    # Generar nuevo código
    cliente.codigo_verificacion = str(random.randint(100000, 999999))
    db.session.commit()
    
    # Enviar de forma asíncrona
    from threading import Thread
    from flask import current_app
    def send_async_code(app, cliente_id, codigo, metodo):
        with app.app_context():
            from models import Cliente
            c = Cliente.query.get(cliente_id)
            if c:
                NotificationService.send_verification_code(c, codigo, metodo)

    Thread(target=send_async_code, args=(current_app._get_current_object(), cliente.id, cliente.codigo_verificacion, cliente.metodo_verificacion)).start()
    
    return jsonify({'message': 'Código reenviado'}), 200

@clients_bp.route('/api/auth/forgot-password', methods=['POST'])
@limiter.limit("3 per hour")
def forgot_password():
    email = request.json.get('email')
    cliente = Cliente.query.filter_by(email=email).first()
    if cliente:
        token = create_access_token(identity=str(cliente.id), additional_claims={'purpose': 'password_reset'}, expires_delta=timedelta(hours=1))
        NotificationService.send_password_reset_email(cliente.email, token, cliente.nombre)
    return jsonify({'message': 'Si el email existe, se ha enviado un enlace'}), 200

@clients_bp.route('/api/auth/reset-password', methods=['POST'])
@limiter.limit("5 per hour")
def reset_password():
    data = request.json
    try:
        decoded = decode_token(data.get('token'))
        if decoded.get('purpose') != 'password_reset': raise Exception("Invalid token purpose")
        cliente = Cliente.query.get(decoded['sub'])
        if cliente:
            cliente.set_password(data.get('password'))
            db.session.commit()
            return jsonify({'message': 'Contraseña actualizada'}), 200
    except:
        pass
    return jsonify({'error': 'Token inválido o expirado'}), 400

@clients_bp.route('/api/clientes/verify', methods=['GET'])
@jwt_required()
def verify_token_cliente():
    """Verificar token JWT para cliente"""
    cliente_id = get_jwt_identity()
    return jsonify({
        'cliente': {
            'id': int(cliente_id),
            'authenticated': True
        }
    }), 200

@clients_bp.route('/api/clientes/me', methods=['PUT'])
@jwt_required()
def update_profile():
    cliente_id = get_jwt_identity()
    cliente = Cliente.query.get(cliente_id)
    if not cliente:
        return jsonify({'error': 'Cliente no encontrado'}), 404
        
    data = request.json
    if 'nombre' in data:
        cliente.nombre = data['nombre']
    if 'telefono' in data:
        cliente.telefono = data['telefono']
    
    db.session.commit()
    return jsonify(cliente.to_dict()), 200

@clients_bp.route('/api/clientes/change-password', methods=['POST'])
@jwt_required()
def change_password():
    cliente_id = get_jwt_identity()
    cliente = Cliente.query.get(cliente_id)
    if not cliente:
        return jsonify({'error': 'Cliente no encontrado'}), 404
        
    data = request.json
    old_password = data.get('old_password')
    new_password = data.get('new_password')
    
    if not old_password or not new_password:
        return jsonify({'error': 'Faltan datos'}), 400
        
    if not cliente.check_password(old_password):
        return jsonify({'error': 'Contraseña actual incorrecta'}), 400
        
    if len(new_password) < 8:
         return jsonify({'error': 'La nueva contraseña debe tener al menos 8 caracteres'}), 400
         
    cliente.set_password(new_password)
    db.session.commit()
    
    return jsonify({'message': 'Contraseña actualizada correctamente'}), 200

@clients_bp.route('/api/clientes/me/orders', methods=['GET'])
@jwt_required()
def get_my_orders():
    cliente_id = get_jwt_identity()
    cliente = Cliente.query.get(cliente_id)
    if not cliente:
        return jsonify({'error': 'Cliente no encontrado'}), 404
        
    # Buscar pedidos por email del cliente
    pedidos = Pedido.query.filter_by(cliente_email=cliente.email).order_by(Pedido.created_at.desc()).all()
    
    return jsonify([p.to_dict() for p in pedidos]), 200
