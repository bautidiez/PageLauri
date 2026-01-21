import requests

BACKEND_URL = "https://elvestuario-backend.onrender.com"
SECRET_KEY = "5qWRFsY2VW7CE3-p-pQWRl1DEA"
TARGET_PASSWORD = "ElVestuario2024!Admin"

print("="*60)
print("RESET DEFINTIVO DE CONTRASEÑA")
print("="*60)

# Resetear password MANDANDO la clave deseada
print(f"\n1. Forzando reset de contraseña a: '{TARGET_PASSWORD}'...")
r = requests.post(
    f"{BACKEND_URL}/api/auth/emergency-reset-admin",
    json={
        "secret": SECRET_KEY,
        "new_password": TARGET_PASSWORD
    }
)
print(f"   Status: {r.status_code}")
print(f"   Response: {r.text}")

# Probar login inmediatamente
print(f"\n2. Verificando login con la misma clave...")
r = requests.post(
    f"{BACKEND_URL}/api/auth/login",
    json={"username": "admin", "password": TARGET_PASSWORD}
)
print(f"   Status: {r.status_code}")
if r.status_code == 200:
    print("   ✅ ¡TODO LISTO! El login funciona correctamente.")
else:
    print(f"   ❌ ERROR CRITICO: El login sigue fallando: {r.text}")
