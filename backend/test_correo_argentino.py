import requests
import os
import json

def test_correo_argentino():
    # Placeholders for credentials
    user = os.environ.get('CORREO_ARG_USER')
    password = os.environ.get('CORREO_ARG_PASS')
    customer_id = os.environ.get('CORREO_ARG_CUSTOMER_ID')
    
    api_base = "https://api.correoargentino.com.ar/micorreo/v1"
    
    if not user or not password or not customer_id:
        print("Missing credentials in .env")
        return

    print(f"Testing Correo Argentino Auth for user: {user}...")
    try:
        auth = (user, password)
        token_res = requests.post(f"{api_base}/token", auth=auth, timeout=10)
        print(f"Auth Status: {token_res.status_code}")
        
        if token_res.status_code == 200:
            token = token_res.json().get('token')
            print("Token obtained successfully.")
            
            print("\nTesting Rate calculation...")
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            payload = {
                "customerId": customer_id,
                "postalCodeOrigin": "1406",
                "postalCodeDestination": "1640",
                "dimensions": {
                    "weight": 1000,
                    "height": 10,
                    "width": 10,
                    "length": 10
                }
            }
            rate_res = requests.post(f"{api_base}/rates", json=payload, headers=headers, timeout=10)
            print(f"Rate Status: {rate_res.status_code}")
            print(f"Response: {rate_res.text}")
        else:
            print(f"Auth Error: {token_res.text}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_correo_argentino()
