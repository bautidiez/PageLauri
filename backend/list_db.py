from app import app
from models import db
from sqlalchemy import inspect

def list_tables():
    with app.app_context():
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        print("--- TABLAS ENCONTRADAS ---")
        for table in tables:
            print(f"- {table}")
            columns = inspector.get_columns(table)
            for column in columns:
                print(f"  * {column['name']} ({column['type']})")

if __name__ == "__main__":
    list_tables()
