from sqlalchemy import text

def repair_db_sqlalchemy(db):
    print("Checking for 'metodo_verificacion' column in 'clientes' using SQLAlchemy...")
    try:
        # Intentar una consulta simple para ver si la columna existe
        db.session.execute(text("SELECT metodo_verificacion FROM clientes LIMIT 1"))
        print("Column 'metodo_verificacion' already exists.")
    except Exception:
        db.session.rollback()
        print("Column 'metodo_verificacion' seems to be missing. Attempting to add it...")
        try:
            db.session.execute(text("ALTER TABLE clientes ADD COLUMN metodo_verificacion VARCHAR(20) DEFAULT 'telefono'"))
            db.session.commit()
            print("Successfully added 'metodo_verificacion' column via SQLAlchemy.")
        except Exception as e:
            db.session.rollback()
            print(f"Error adding column via SQLAlchemy: {e}")
