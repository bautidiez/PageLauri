"""
Verificar promociones en la BD usando SQL directo
"""
import psycopg2
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

conn = psycopg2.connect(os.getenv('DATABASE_URL'))
cur = conn.cursor()

# Consultar promociones
cur.execute("""
    SELECT id, alcance, activa, fecha_inicio, fecha_fin, created_at
    FROM promociones_productos
    ORDER BY id
""")

promociones = cur.fetchall()

print(f'Total promociones en BD: {len(promociones)}')
print(f'Fecha actual: {datetime.utcnow()}')
print('\n' + '='*80)

for p in promociones:
    id, alcance, activa, fecha_inicio, fecha_fin, created = p
    vigente = fecha_inicio <= datetime.utcnow() <= fecha_fin if fecha_inicio and fecha_fin else False
    
    print(f'\nPromoción ID {id}:')
    print(f'  Alcance: {alcance}')
    print(f'  Activa: {activa}')
    print(f'  Inicio: {fecha_inicio}')
    print(f'  Fin: {fecha_fin}')
    print(f'  ¿Vigente ahora?: {vigente}')
    print(f'  Creada: {created}')

# Contar productos vinculados
cur.execute("""
    SELECT promocion_id, COUNT(*) 
    FROM promocion_productos_link 
    GROUP BY promocion_id
""")
vinculados = cur.fetchall()

print('\n' + '='*80)
print('\nProductos vinculados a promociones:')
for promo_id, count in vinculados:
    print(f'  Promoción {promo_id}: {count} productos')

cur.close()
conn.close()
