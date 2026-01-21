import requests

BACKEND_URL = "https://elvestuario-backend.onrender.com"

print("--- Database Info ---")
try:
    r = requests.get(f"{BACKEND_URL}/")
    if r.status_code == 200:
        # Looking for the debug print in the home response if I added it, 
        # but I didn't add the URI to the response for security.
        # Let's check the /api/health if it exists.
        print("Backend root is accessible.")
        
    r_health = requests.get(f"{BACKEND_URL}/api/health")
    if r_health.status_code == 200:
        print(f"Health check: {r_health.text}")
    else:
        print(f"Health check failed: {r_health.status_code}")
except Exception as e:
    print(f"Error: {e}")
