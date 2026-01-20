import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()
conn = psycopg2.connect(os.getenv('DATABASE_URL'))
cur = conn.cursor()

cur.execute("SELECT id, alcance, activa, fecha_inicio::text, fecha_fin::text FROM promociones_productos")
promos = cur.fetchall()

print(f'Promociones totales: {len(promos)}')
for p in promos:
    print(f'ID: {p[0]}, Alcance: {p[1]}, Activa: {p[2]}, Inicio: {p[3]}, Fin: {p[4]}')

cur.execute("SELECT promocion_id, COUNT(*) FROM promocion_productos_link GROUP BY promocion_id")
links = cur.fetchall()
print(f'\nProductos por promoción:')
for link in links:
    print(f'  Promo {link[0]}: {link[1]} productos')

cur.close()
conn.close()
