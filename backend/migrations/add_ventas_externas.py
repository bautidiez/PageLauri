"""
Migration script to add ventas_externas table
Creates table for tracking external sales made outside the web store
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__) + '/..')

from flask import Flask
from models import db, VentaExterna

def migrate():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///instance/tienda.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    
    with app.app_context():
        # Create only the VentaExterna table
        # This will create the table with all columns and indexes defined in the model
        inspector = db.inspect(db.engine)
        if 'ventas_externas' not in inspector.get_table_names():
            # Create table from model
            VentaExterna.__table__.create(db.engine)
            print("✅ Migration completed: ventas_externas table created successfully")
        else:
            print("ℹ️  Table ventas_externas already exists")

if __name__ == '__main__':
    migrate()
