from app import app, db
from sqlalchemy import text

def migrate():
    with app.app_context():
        engine = db.engine
        with engine.connect() as conn:
            print("Starting migration...")
            
            queries = [
                "ALTER TABLE promociones_productos ADD COLUMN IF NOT EXISTS es_cupon BOOLEAN DEFAULT FALSE;",
                "ALTER TABLE promociones_productos ADD COLUMN IF NOT EXISTS codigo VARCHAR(50);",
                "ALTER TABLE promociones_productos ADD COLUMN IF NOT EXISTS envio_gratis BOOLEAN DEFAULT FALSE;",
            ]
            
            for q in queries:
                try:
                    conn.execute(text(q))
                    print(f"Executed: {q}")
                except Exception as e:
                    print(f"Error executing {q}: {e}")
            
            # Constraint for unique code
            try:
                # Check if constraint exists, if not add it. 
                # Postgres "CREATE UNIQUE INDEX IF NOT EXISTS" is safe.
                conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS idx_promociones_codigo ON promociones_productos (codigo);"))
                print("Created unique index for codigo")
            except Exception as e:
                 print(f"Error creating index: {e}")
                 
            conn.commit()
            print("Migration completed successfully.")

if __name__ == "__main__":
    migrate()
