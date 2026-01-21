import requests

BACKEND_URL = "https://elvestuario-backend.onrender.com"
SECRET_KEY = "5qWRFsY2VW7CE3-p-pQWRl1DEA"

print("="*60)
print("DIAGNOSTICO DE LOGIN")
print("="*60)

# Resetear password
print("\nReseteando password del admin...")
r = requests.post(
    f"{BACKEND_URL}/api/auth/emergency-reset-admin",
    json={"secret": SECRET_KEY}
)
print(f"Status: {r.status_code}")
print(r.text)

# Probar login
print("\nProbando login...")
r = requests.post(
    f"{BACKEND_URL}/api/auth/login",
    json={"username": "admin", "password": "ElVestuario2024!Admin"}
)
print(f"Status: {r.status_code}")
if r.status_code == 200:
    print("LOGIN EXITOSO!")
else:
    print(f"Error: {r.text}")
