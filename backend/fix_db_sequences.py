"""
Script to synchronize PostgreSQL sequences with the maximum ID in each table.
This prevents 'duplicate key value violates unique constraint' errors (UniqueViolation).
"""
import psycopg2
import os
from urllib.parse import urlparse

# Use DATABASE_URL if available (production), otherwise fallback to local
# For local use, you can set the environment variable or edit the string below
db_url = os.environ.get('DATABASE_URL') or "postgresql://postgres:bauti123@127.0.0.1:5432/elvestuario"

def fix_sequences():
    try:
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        
        # Tables to check
        tables = [
            'categorias',
            'productos',
            'promociones_productos',
            'pedidos',
            'clientes',
            'usuarios',
            'talles',
            'colores',
            'stock_talles',
            'detalles_pedidos',
            'metodos_pago'
        ]
        
        print("Starting sequence synchronization...")
        
        for table in tables:
            try:
                # Get the primary key column name (usually 'id')
                # For safety, we assume 'id' for these tables
                pk_column = 'id'
                
                # The sequence name usually follows the pattern '{table}_{pk_column}_seq'
                seq_name = f"{table}_{pk_column}_seq"
                
                print(f"Checking table: {table} (sequence: {seq_name})")
                
                # Check if the sequence exists
                cur.execute(f"SELECT to_regclass(%s)", (seq_name,))
                if cur.fetchone()[0] is None:
                    print(f"  ⚠️ Sequence {seq_name} not found, skipping.")
                    continue
                
                # Get max ID
                cur.execute(f"SELECT MAX({pk_column}) FROM {table}")
                max_id = cur.fetchone()[0]
                
                if max_id is None:
                    print(f"  ℹ️ Table is empty, skipping.")
                    continue
                
                # Update sequence
                # setval(sequence, max_id) sets it so the NEXT value will be max_id + 1
                cur.execute(f"SELECT setval(%s, %s)", (seq_name, max_id))
                print(f"  ✅ Sequence updated to {max_id}. Next ID will be {max_id + 1}.")
                
            except Exception as e:
                print(f"  ❌ Error processing {table}: {str(e)}")
                conn.rollback()
                continue
        
        conn.commit()
        print("\nAll sequences synchronization completed successfully.")
        
    except Exception as e:
        print(f"CRITICAL ERROR: {str(e)}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    fix_sequences()
