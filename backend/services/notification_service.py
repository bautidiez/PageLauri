from flask_mail import Message
import requests
import os

class NotificationService:
    @staticmethod
    def send_order_confirmation(pedido):
        """Envía notificaciones de pedido recibido/pendiente"""
        # Aquí se enviaría el primer email/WhatsApp si se desea
        pass

    @staticmethod
    def send_payment_confirmation(pedido):
        """Envía notificaciones cuando el pago se acredita"""
        from app import mail # Importación diferida para evitar ciclos
        
        # 1. Notificación por Email
        msg = Message(
            f"Pago Confirmado - Pedido #{pedido.numero_pedido}",
            recipients=[pedido.cliente_email]
        )
        msg.body = f"""
        Hola {pedido.cliente_nombre}, tu pago del pedido #{pedido.numero_pedido} se acreditó correctamente.
        
        Detalles del pedido:
        Total: ${pedido.total}
        Estado: PAGADO
        
        ¡Gracias por tu compra!
        """
        try:
            mail.send(msg)
        except Exception as e:
            print(f"Error enviando email: {e}")

        # 2. Notificación por WhatsApp (Meta Cloud API)
        # Se asume que existen variables de entorno configuradas
        wa_token = os.environ.get('WA_TOKEN')
        wa_phone_id = os.environ.get('WA_PHONE_ID')
        
        if wa_token and wa_phone_id:
            url = f"https://graph.facebook.com/v17.0/{wa_phone_id}/messages"
            headers = {
                "Authorization": f"Bearer {wa_token}",
                "Content-Type": "application/json"
            }
            payload = {
                "messaging_product": "whatsapp",
                "to": pedido.cliente_telefono,
                "type": "template",
                "template": {
                    "name": "confirmacion_pago", # Nombre del template aprobado en Meta
                    "language": { "code": "es" },
                    "components": [
                        {
                            "type": "body",
                            "parameters": [
                                { "type": "text", "text": pedido.cliente_nombre },
                                { "type": "text", "text": pedido.numero_pedido },
                                { "type": "text", "text": str(pedido.total) }
                            ]
                        }
                    ]
                }
            }
            try:
                requests.post(url, json=payload, headers=headers)
            except Exception as e:
                print(f"Error enviando WhatsApp: {e}")
        else:
            print("WhatsApp no configurado. Simulando envío para pedido #" + pedido.numero_pedido)
            print(f"WHATSAPP A {pedido.cliente_telefono}: Hola {pedido.cliente_nombre}, pago confirmado por ${pedido.total}")

    @staticmethod
    def send_password_reset_email(email, token, nombre):
        """Envía email para restablecer contraseña"""
        from app import mail
        
        # Link al frontend (asumiendo que corre en el mismo host o configurado)
        # En producción debería ser una variable de entorno FRONTEND_URL
        frontend_url = os.environ.get('FRONTEND_URL', 'http://localhost:4200')
        reset_link = f"{frontend_url}/reset-password?token={token}"
        
        msg = Message(
            "Restablecer Contraseña - El Vestuario",
            recipients=[email]
        )
        msg.body = f"""
        Hola {nombre},
        
        Recibimos una solicitud para restablecer tu contraseña.
        Haz clic en el siguiente enlace para crear una nueva contraseña:
        
        {reset_link}
        
        Si no solicitaste esto, puedes ignorar este correo.
        El enlace expirará en 1 hora.
        
        Saludos,
        El equipo de El Vestuario
        """
        try:
            print(f"DEBUG EMAIL: Enviando reset link a {email}: {reset_link}")
            mail.send(msg)
            return True
        except Exception as e:
            print(f"Error enviando email de reset: {e}")
            return False

    @staticmethod
    def send_verification_code(cliente, codigo, metodo):
        """Envía el código de verificación por email o WhatsApp/SMS"""
        if metodo == 'email':
            api_key = os.environ.get('BREVO_API_KEY')
            if not api_key:
                print("DEBUG NOTIFICACION: BREVO_API_KEY no configurada. No se puede enviar email de verificación.")
                return False
                
            url = "https://api.brevo.com/v3/smtp/email"
            headers = {
                "accept": "application/json",
                "content-type": "application/json",
                "api-key": api_key
            }
            
            payload = {
                "sender": {"name": "El Vestuario", "email": os.environ.get('MAIL_DEFAULT_SENDER', 'elvestuario.r4@gmail.com')},
                "to": [{"email": cliente.email}],
                "subject": "Código de Verificación - El Vestuario",
                "textContent": f"Hola {cliente.nombre}, tu código de verificación es: {codigo}\n\nEste código es necesario para activar tu cuenta."
            }
            
            try:
                print(f"DEBUG NOTIFICACION: Enviando código de verificación a {cliente.email} vía Brevo...", flush=True)
                response = requests.post(url, headers=headers, json=payload, timeout=15)
                return response.status_code in [201, 202, 200]
            except Exception as e:
                print(f"DEBUG NOTIFICACION: Error enviando mail de verificación: {e}")
                return False
        else:
            # 1. Intentar WhatsApp (Meta Cloud API) si están las credenciales
            wa_token = os.environ.get('WA_TOKEN')
            wa_phone_id = os.environ.get('WA_PHONE_ID')
            
            if wa_token and wa_phone_id:
                url = f"https://graph.facebook.com/v17.0/{wa_phone_id}/messages"
                headers = {
                    "Authorization": f"Bearer {wa_token}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "messaging_product": "whatsapp",
                    "to": cliente.telefono,
                    "type": "template",
                    "template": {
                        "name": "verificacion_cuenta", # Nombre del template que debe estar aprobado en Meta
                        "language": { "code": "es" },
                        "components": [
                            {
                                "type": "body",
                                "parameters": [
                                    { "type": "text", "text": cliente.nombre },
                                    { "type": "text", "text": codigo }
                                ]
                            }
                        ]
                    }
                }
                try:
                    print(f"DEBUG NOTIFICACION: Intentando enviar WhatsApp a {cliente.telefono}...", flush=True)
                    response = requests.post(url, json=payload, headers=headers, timeout=10)
                    if response.status_code in [200, 201]:
                        print("DEBUG NOTIFICACION: WhatsApp enviado con éxito vía Meta.", flush=True)
                        return True
                    else:
                        print(f"DEBUG NOTIFICACION: WhatsApp falló (Status: {response.status_code}). Intentando fallback a SMS...", flush=True)
                except Exception as e:
                    print(f"DEBUG NOTIFICACION: Error en WhatsApp Meta: {e}. Intentando fallback a SMS...", flush=True)

            # 2. Fallback a SMS (Brevo) si no hay WhatsApp o falló
            api_key = os.environ.get('BREVO_API_KEY')
            if not api_key:
                print("DEBUG NOTIFICACION: BREVO_API_KEY no configurada. No se puede enviar SMS de fallback.")
                return False

            telefono_limpio = "".join(filter(str.isdigit, cliente.telefono))
            url_sms = "https://api.brevo.com/v3/transactionalSMS/sms"
            headers_sms = {
                "accept": "application/json",
                "content-type": "application/json",
                "api-key": api_key
            }
            
            payload_sms = {
                "type": "transactional",
                "sender": "ElVestuario",
                "recipient": telefono_limpio,
                "content": f"Hola {cliente.nombre}, tu codigo de verificacion El Vestuario es: {codigo}"
            }
            
            try:
                print(f"DEBUG NOTIFICACION: Enviando SMS de fallback a {telefono_limpio} vía Brevo...", flush=True)
                requests.post(url_sms, headers=headers_sms, json=payload_sms, timeout=15)
                return True
            except Exception as e:
                print(f"DEBUG NOTIFICACION: Error en SMS de fallback: {e}")
                return False
