"""Script para verificar el stock en la base de datos"""
import psycopg2

# Conectar a la base de datos
conn = psycopg2.connect(
    host="127.0.0.1",
    port=5432,
    database="elvestuario",
    user="postgres",
    password="bauti123"
)

cur = conn.cursor()

# Buscar Remera 1
cur.execute("SELECT id, nombre FROM productos WHERE nombre LIKE %s LIMIT 1", ('%Remera 1%',))
producto = cur.fetchone()

if producto:
    producto_id, producto_nombre = producto
    print(f"\n✅ Producto encontrado: {producto_nombre} (ID: {producto_id})")
    
    # Buscar stock para este producto
    cur.execute("""
        SELECT st.id, st.producto_id, st.talle_id, st.cantidad, t.nombre as talle_nombre
        FROM stock_talles st
        LEFT JOIN talles t ON st.talle_id = t.id
        WHERE st.producto_id = %s
        ORDER BY t.nombre
    """, (producto_id,))
    
    stock_items = cur.fetchall()
    
    print(f"\n📊 Stock encontrado: {len(stock_items)} registros")
    
    if stock_items:
        print("\nDetalle del stock:")
        for item in stock_items:
            stock_id, prod_id, talle_id, cantidad, talle_nombre = item
            print(f"  - Talle: {talle_nombre or 'N/A'} (ID: {talle_id}) - Cantidad: {cantidad}")
    else:
        print("\n⚠️ NO HAY STOCK REGISTRADO para este producto")
        
    # Mostrar todos los talles disponibles
    print("\n📏 Talles en el sistema:")
    cur.execute("SELECT id, nombre FROM talles ORDER BY nombre")
    talles = cur.fetchall()
    for talle_id, talle_nombre in talles:
        print(f"  - {talle_nombre} (ID: {talle_id})")
        
else:
    print("\n❌ Producto 'Remera 1' no encontrado")
    
    # Mostrar productos que contienen "Remera"
    print("\n🔍 Productos que contienen 'Remera':")
    cur.execute("SELECT id, nombre FROM productos WHERE nombre LIKE %s LIMIT 10", ('%Remera%',))
    remeras = cur.fetchall()
    for prod_id, nombre in remeras:
        print(f"  - {nombre} (ID: {prod_id})")

cur.close()
conn.close()
