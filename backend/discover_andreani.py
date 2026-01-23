import requests
import os

def discover_andreani_info():
    credential_id = "UHltZXxTVHBkcjBweXdPTEpoVDYwMnpDdWlYSGNuRk44aE81clZtNmdlcmZVSGw4PQ=="
    headers = {'X-Authorization-Id': credential_id}
    
    # Try multiple potential "info" endpoints
    endpoints = [
        "https://api.andreani.com/v1/contratos",
        "https://api.andreani.com/v1/cuentas",
        "https://api.andreani.com/v1/usuarios/me",
        "https://api.andreani.com/v1/cliente",
        "https://api.andreani.com/v2/cuentas",
        "https://api.andreani.com/v1/configuracion"
    ]
    
    for url in endpoints:
        print(f"\n--- Testing Endpoint: {url} ---")
        try:
            response = requests.get(url, headers=headers, timeout=10)
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                print(f"SUCCESS! Response: {response.text}")
            else:
                print(f"Response: {response.text[:200]}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    discover_andreani_info()
