import requests
import time
import os

BASE_URL = "http://localhost:5000/api"
EMAIL = f"test_reset_{int(time.time())}@test.com"
PASSWORD = "OldPassword1"
NEW_PASSWORD = "NewPassword2"

def run_test():
    print(f"1. Registering user {EMAIL}...")
    res = requests.post(f"{BASE_URL}/clientes", json={
        "nombre": "Test User",
        "email": EMAIL,
        "password": PASSWORD
    })
    if res.status_code != 201:
        print("Registration failed:", res.text)
        return
    print("User registered.")

    print("2. Requesting password reset...")
    res = requests.post(f"{BASE_URL}/auth/forgot-password", json={
        "email": EMAIL
    })
    if res.status_code != 200:
        print("Forgot password request failed:", res.text)
        return
    print("Reset requested.")

    # Give it a moment to write the file
    time.sleep(1)
    
    if not os.path.exists('latest_token.txt'):
        print("Error: Token file not found. Make sure the backend is running with the modified service.")
        return

    with open('latest_token.txt', 'r') as f:
        token = f.read().strip()
    print(f"Token captured: {token[:20]}...")

    print("3. Resetting password...")
    res = requests.post(f"{BASE_URL}/auth/reset-password", json={
        "token": token,
        "password": NEW_PASSWORD
    })
    if res.status_code != 200:
        print("Reset password failed:", res.text)
        return
    print("Password reset successful.")

    print("4. Logging in with NEW password...")
    res = requests.post(f"{BASE_URL}/clientes/login", json={
        "email": EMAIL,
        "password": NEW_PASSWORD
    })
    if res.status_code == 200:
        print("SUCCESS! Login with new password worked.")
    else:
        print("Login failed:", res.text)

if __name__ == "__main__":
    run_test()
