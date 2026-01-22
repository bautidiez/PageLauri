import os
import sys

# Add the parent directory to the path so we can import the app and models
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from app import app
    from models import Talle
    
    with app.app_context():
        talles = Talle.query.all()
        print("Talles disponibles:")
        for t in talles:
            print(f"- {t.nombre} (ID: {t.id})")
            
except Exception as e:
    print(f"Error listing talles: {str(e)}")
