from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, create_access_token, get_jwt_identity, decode_token
from extensions import limiter
from models import Cliente, db
from services.notification_service import NotificationService
import re
import logging
import random
import time
from datetime import timedelta

logger = logging.getLogger(__name__)
clients_bp = Blueprint('clients', __name__)

@clients_bp.route('/api/clientes', methods=['POST'])
@limiter.limit("5 per hour")
def registrar_cliente():
    data = request.json
    if not data.get('nombre') or not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Faltan campos requeridos'}), 400
    
    password = data['password']
    if len(password) < 8 or not re.search(r'[A-Z]', password) or not re.search(r'[a-z]', password) or not re.search(r'\d', password):
        return jsonify({'error': 'La contraseña no cumple los requisitos de seguridad'}), 400
    
    if Cliente.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email ya registrado'}), 400
    
    cliente = Cliente(
        nombre=data['nombre'],
        email=data['email'],
        telefono=data.get('telefono'),
        metodo_verificacion=data.get('metodo_verificacion', 'telefono'),
        acepta_newsletter=data.get('acepta_newsletter', True)
    )
    cliente.set_password(password)
    cliente.codigo_verificacion = str(random.randint(100000, 999999))
    
    db.session.add(cliente)
    db.session.commit()
    
    # Enviar código de forma asíncrona para no demorar la respuesta
    from threading import Thread
    from flask import current_app
    def send_async_code(app, cliente_id, codigo, metodo):
        with app.app_context():
            from models import Cliente
            c = Cliente.query.get(cliente_id)
            if c:
                NotificationService.send_verification_code(c, codigo, metodo)

    Thread(target=send_async_code, args=(current_app._get_current_object(), cliente.id, cliente.codigo_verificacion, cliente.metodo_verificacion)).start()

    logger.info(f"🆕 REGISTRO OK: {cliente.email} - Verif: {cliente.metodo_verificacion}")
    return jsonify(cliente.to_dict()), 201

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
        if not cliente.telefono_verificado:
            return jsonify({'error': 'Requiere verificación', 'requires_verification': True, 'email': email}), 403
            
        access_token = create_access_token(identity=str(cliente.id))
        return jsonify({'access_token': access_token, 'cliente': cliente.to_dict()}), 200
    
    return jsonify({'error': 'Credenciales inválidas'}), 401

@clients_bp.route('/api/clientes/verify-code', methods=['POST'])
@limiter.limit("5 per minute")
def verificar_codigo():
    data = request.json
    cliente = Cliente.query.filter_by(email=data.get('email')).first()
    if cliente and cliente.codigo_verificacion == str(data.get('codigo')):
        cliente.telefono_verificado = True
        cliente.codigo_verificacion = None
        db.session.commit()
        return jsonify({'message': 'Verificado'}), 200
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
