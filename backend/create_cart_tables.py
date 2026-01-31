from app import app, db
from models import Carrito, ItemCarrito
from sqlalchemy import text

if __name__ == "__main__":
    with app.app_context():
        print("Creating cart tables...")
        try:
            # Create tables only if they don't exist
            db.create_all()
            print("Tables 'carritos' and 'items_carrito' created successfully (if they didn't exist).")
            
            # Verify creation
            insp = db.inspect(db.engine)
            tables = insp.get_table_names()
            if 'carritos' in tables and 'items_carrito' in tables:
                print("VERIFICATION: Tables exist.")
            else:
                print("ERROR: Tables not found after creation.")
                
        except Exception as e:
            print(f"Error creating tables: {e}")
