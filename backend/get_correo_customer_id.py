import requests
import os
from dotenv import load_dotenv

load_dotenv()

def get_customer_id():
    user = os.environ.get('CORREO_ARG_USER', 'Laureano')
    password = os.environ.get('CORREO_ARG_PASS', 'Tomilauri2025')
    email = os.environ.get('CORREO_ARG_EMAIL')
    
    if not email or email == 'tu_email@ejemplo.com':
        print("❌ Necesito el EMAIL con el que te registraste en MiCorreo.")
        print("Por favor, actualiza CORREO_ARG_EMAIL en el .env con tu email y vuelve a ejecutar este script.")
        return
    
    api_base = "https://api.correoargentino.com.ar/micorreo/v1"
    
    print(f"🔐 Autenticando con MiCorreo...")
    try:
        # Paso 1: Obtener el token JWT
        auth = (user, password)
        token_res = requests.post(f"{api_base}/token", auth=auth, timeout=10)
        
        if token_res.status_code != 200:
            print(f"❌ Error de autenticación: {token_res.status_code}")
            print(f"Respuesta: {token_res.text}")
            return
        
        token = token_res.json().get('token')
        print(f"✅ Token obtenido exitosamente")
        
        # Paso 2: Validar usuario y obtener Customer ID
        print(f"\n📋 Obteniendo Customer ID para el email: {email}...")
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        validate_payload = {
            "email": email,
            "password": password
        }
        
        validate_res = requests.post(
            f"{api_base}/users/validate",
            json=validate_payload,
            headers=headers,
            timeout=10
        )
        
        if validate_res.status_code == 200:
            data = validate_res.json()
            customer_id = data.get('customerId')
            print(f"\n✅ ¡Customer ID encontrado: {customer_id}!")
            print(f"\n📝 Agrega esta línea a tu .env:")
            print(f"CORREO_ARG_CUSTOMER_ID={customer_id}")
            return customer_id
        else:
            print(f"❌ Error al validar: {validate_res.status_code}")
            print(f"Respuesta: {validate_res.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    get_customer_id()
