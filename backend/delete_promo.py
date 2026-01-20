import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()
conn = psycopg2.connect(os.getenv('DATABASE_URL'))
cur = conn.cursor()

print('Eliminando promoción ID 1...')

# Primero eliminar los vínculos
cur.execute("DELETE FROM promocion_productos_link WHERE promocion_id = 1")
links_deleted = cur.rowcount
print(f'  - Eliminados {links_deleted} vínculos producto-promoción')

cur.execute("DELETE FROM promocion_categorias_link WHERE promocion_id = 1")
cat_links_deleted = cur.rowcount
print(f'  - Eliminados {cat_links_deleted} vínculos categoría-promoción')

# Ahora eliminar la promoción
cur.execute("DELETE FROM promociones_productos WHERE id = 1")
promo_deleted = cur.rowcount
print(f'  - Eliminada {promo_deleted} promoción')

conn.commit()

# Verificar
cur.execute("SELECT COUNT(*) FROM promociones_productos")
total = cur.fetchone()[0]
print(f'\n✓ Promociones restantes en BD: {total}')

cur.close()
conn.close()

print('\n✓ Promoción eliminada exitosamente!')
