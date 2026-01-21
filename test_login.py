#!/usr/bin/env python3
"""
Script para probar y arreglar el login del admin en producción
"""
import requests
import json

BACKEND_URL = "https://elvestuario-backend.onrender.com"
SECRET_KEY = "5qWRFsY2VW7CE3-p-pQWRl1DEA"

print("=" * 60)
print("DIAGNÓSTICO Y ARREGLO DE LOGIN - El Vestuario")
print("=" * 60)

# 1. Verificar que el backend responda
print("\n1. Verificando backend...")
try:
    r = requests.get(f"{BACKEND_URL}/", timeout=10)
    print(f"   ✓ Backend responde: {r.status_code}")
    if r.status_code == 200:
        print(f"   {r.json()}")
except Exception as e:
    print(f"   ✗ Error: {e}")
    exit(1)

# 2. Verificar health
print("\n2. Verificando /api/health...")
try:
    r = requests.get(f"{BACKEND_URL}/api/health", timeout=10)
    print(f"   ✓ Health check: {r.status_code}")
except Exception as e:
    print(f"   ⚠ Warning: {e}")

# 3. Resetear contraseña del admin
print("\n3. Reseteando contraseña del admin...")
try:
    r = requests.post(
        f"{BACKEND_URL}/api/auth/emergency-reset-admin",
        json={"secret": SECRET_KEY},
        timeout=10
    )
    print(f"   Status: {r.status_code}")
    if r.status_code == 200:
        print(f"   ✓ {r.json()}")
    else:
        print(f"   ✗ Error: {r.text}")
        exit(1)
except Exception as e:
    print(f"   ✗ Error: {e}")
    exit(1)

# 4. Intentar login
print("\n4. Probando login con admin/ElVestuario2024!Admin...")
try:
    r = requests.post(
        f"{BACKEND_URL}/api/auth/login",
        json={"username": "admin", "password": "ElVestuario2024!Admin"},
        timeout=10
    )
    print(f"   Status: {r.status_code}")
    if r.status_code == 200:
        print(f"   ✓ ¡LOGIN EXITOSO!")
        data = r.json()
        print(f"   Token: {data.get('access_token', '')[:50]}...")
    else:
        print(f"   ✗ Login falló: {r.text}")
except Exception as e:
    print(f"   ✗ Error: {e}")

print("\n" + "=" * 60)
print("DIAGNÓSTICO COMPLETADO")
print("=" * 60)
