# Guía Paso a Paso - El Vestuario

## 📋 Resumen del Proyecto

Estás desarrollando una tienda online llamada **"El Vestuario"** con las siguientes características:

- **Frontend:** Angular
- **Backend:** Python con Flask
- **Base de datos:** SQLite (desarrollo) / PostgreSQL (producción)
- **Catálogo:** 60 remeras + 15 shorts de fútbol
- **Métodos de pago:** Transferencia, tarjeta de débito/crédito
- **Panel de administración:** Gestión completa de productos, stock, precios, promociones
- **Integración de envíos:** Andreani, Correo Argentino, Tienda Nube

---

## 🚀 PASO 1: Configuración del Backend

### 1.1 Estructura del Proyecto

El proyecto tiene la siguiente estructura:

```
elvestuario/
├── backend/
│   ├── app.py              # Aplicación principal Flask
│   ├── models.py           # Modelos de base de datos
│   ├── routes.py           # Rutas API
│   ├── init_data.py        # Script de inicialización de datos
│   ├── requirements.txt    # Dependencias Python
│   ├── .env.example        # Ejemplo de variables de entorno
│   ├── .gitignore          # Archivos a ignorar en git
│   ├── README.md           # Documentación del backend
│   └── static/
│       └── uploads/         # Carpeta para imágenes de productos
└── frontend/               # (Se creará después)
```

### 1.2 Instalación de Python y Dependencias

**Paso 1:** Asegúrate de tener Python 3.8 o superior instalado.

**Paso 2:** Abre una terminal en la carpeta `backend/` y crea un entorno virtual:

```bash
cd backend
python -m venv venv
```

**Paso 3:** Activa el entorno virtual:

- **Windows:**
```bash
venv\Scripts\activate
```

- **Linux/Mac:**
```bash
source venv/bin/activate
```

**Paso 4:** Instala las dependencias:

```bash
pip install -r requirements.txt
```

Esto instalará:
- Flask (framework web)
- Flask-SQLAlchemy (ORM para base de datos)
- Flask-CORS (para permitir peticiones desde Angular)
- Flask-JWT-Extended (autenticación JWT)
- Werkzeug (utilidades, incluye seguridad de contraseñas)
- python-dotenv (para variables de entorno)

### 1.3 Configuración de Variables de Entorno

**Paso 1:** Crea un archivo `.env` en la carpeta `backend/`:

```bash
# En Windows PowerShell
Copy-Item .env.example .env

# En Linux/Mac
cp .env.example .env
```

**Paso 2:** Edita el archivo `.env` y cambia las claves secretas:

```env
SECRET_KEY=tu-clave-secreta-muy-segura-aqui-cambiar
JWT_SECRET_KEY=tu-jwt-secret-key-muy-segura-aqui-cambiar
DATABASE_URL=sqlite:///elvestuario.db
```

⚠️ **IMPORTANTE:** En producción, usa claves seguras y aleatorias.

### 1.4 Inicialización de la Base de Datos

**Paso 1:** Ejecuta el script de inicialización:

```bash
python init_data.py
```

Este script creará:
- ✅ Talles (XS, S, M, L, XL, XXL)
- ✅ Categorías (Remeras, Shorts)
- ✅ Tipos de promoción (2x1, 3x2, descuentos)
- ✅ Métodos de pago (transferencia, tarjeta débito/crédito)
- ✅ 60 productos de ejemplo (remeras)
- ✅ 15 productos de ejemplo (shorts)
- ✅ Stock inicial para cada producto-talle

**Paso 2:** Verifica que se creó el archivo `elvestuario.db` en la carpeta `backend/`.

### 1.5 Ejecutar el Servidor Backend

**Paso 1:** Ejecuta el servidor:

```bash
python app.py
```

**Paso 2:** Verifica que el servidor esté corriendo. Deberías ver algo como:

```
 * Running on http://0.0.0.0:5000
```

**Paso 3:** Prueba que funciona abriendo en tu navegador:

```
http://localhost:5000/api/productos
```

Deberías ver un JSON con la lista de productos.

---

## 🔐 PASO 2: Credenciales de Administrador

Por defecto, se crea un administrador con:

- **Usuario:** `admin`
- **Contraseña:** `admin123`

⚠️ **IMPORTANTE:** Cambia estas credenciales en producción.

Para cambiar la contraseña, puedes:
1. Eliminar el archivo `elvestuario.db` y ejecutar `python app.py` de nuevo
2. O crear un script para cambiar la contraseña (se puede agregar después)

---

## 📡 PASO 3: Endpoints de la API

### 3.1 Autenticación

**Login de administrador:**
```http
POST /api/auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "admin123"
}
```

**Respuesta:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "admin": {
    "id": 1,
    "username": "admin",
    "email": "admin@elvestuario.com"
  }
}
```

**Verificar token:**
```http
GET /api/auth/verify
Authorization: Bearer <token>
```

### 3.2 Productos (Público)

**Listar productos:**
```http
GET /api/productos
GET /api/productos?categoria_id=1
GET /api/productos?destacados=true
```

**Obtener un producto:**
```http
GET /api/productos/1
```

### 3.3 Productos (Admin - requiere JWT)

**Crear producto:**
```http
POST /api/admin/productos
Authorization: Bearer <token>
Content-Type: application/json

{
  "nombre": "Remera Nueva",
  "descripcion": "Descripción del producto",
  "precio_base": 15000,
  "precio_descuento": null,
  "categoria_id": 1,
  "activo": true,
  "destacado": false,
  "stock_talles": [
    {"talle_id": 1, "cantidad": 10},
    {"talle_id": 2, "cantidad": 10}
  ]
}
```

**Actualizar producto:**
```http
PUT /api/admin/productos/1
Authorization: Bearer <token>
Content-Type: application/json

{
  "nombre": "Remera Actualizada",
  "precio_base": 16000
}
```

**Eliminar producto:**
```http
DELETE /api/admin/productos/1
Authorization: Bearer <token>
```

### 3.4 Gestión de Stock (Admin)

**Listar stock:**
```http
GET /api/admin/stock
GET /api/admin/stock?producto_id=1
```

**Crear/Actualizar stock:**
```http
POST /api/admin/stock
Authorization: Bearer <token>
Content-Type: application/json

{
  "producto_id": 1,
  "talle_id": 2,
  "cantidad": 15
}
```

**Actualizar stock:**
```http
PUT /api/admin/stock/1
Authorization: Bearer <token>
Content-Type: application/json

{
  "cantidad": 20
}
```

### 3.5 Imágenes (Admin)

**Subir imagen:**
```http
POST /api/admin/productos/1/imagenes
Authorization: Bearer <token>
Content-Type: multipart/form-data

imagen: <archivo>
es_principal: true
orden: 0
```

**Eliminar imagen:**
```http
DELETE /api/admin/imagenes/1
Authorization: Bearer <token>
```

### 3.6 Promociones

**Listar promociones activas:**
```http
GET /api/promociones
GET /api/promociones?producto_id=1
```

**Crear promoción (Admin):**
```http
POST /api/admin/promociones
Authorization: Bearer <token>
Content-Type: application/json

{
  "producto_id": 1,
  "tipo_promocion_id": 3,  // 3 = "2x1"
  "valor": null,
  "activa": true,
  "fecha_inicio": "2024-01-01T00:00:00",
  "fecha_fin": "2024-12-31T23:59:59"
}
```

**Tipos de promoción disponibles:**
- `descuento_porcentaje`: Descuento por porcentaje (valor = %)
- `descuento_fijo`: Descuento fijo en pesos (valor = monto)
- `2x1`: Llevas 2, pagas 1
- `3x2`: Llevas 3, pagas 2
- `llevas_3_paga_2`: Llevas 3, pagas 2 (alternativa)

### 3.7 Pedidos

**Crear pedido (Público):**
```http
POST /api/pedidos
Content-Type: application/json

{
  "cliente_nombre": "Juan Pérez",
  "cliente_email": "juan@example.com",
  "cliente_telefono": "1234567890",
  "cliente_direccion": "Calle Falsa 123",
  "cliente_codigo_postal": "1000",
  "cliente_localidad": "Buenos Aires",
  "cliente_provincia": "CABA",
  "metodo_pago_id": 1,
  "metodo_envio": "correo_argentino",
  "items": [
    {
      "producto_id": 1,
      "talle_id": 2,
      "cantidad": 2
    }
  ]
}
```

**Listar pedidos (Admin):**
```http
GET /api/admin/pedidos
GET /api/admin/pedidos?estado=pendiente
Authorization: Bearer <token>
```

**Actualizar estado de pedido (Admin):**
```http
PUT /api/admin/pedidos/1
Authorization: Bearer <token>
Content-Type: application/json

{
  "estado": "en_preparacion",
  "notas": "Pedido en preparación"
}
```

Estados posibles: `pendiente`, `confirmado`, `en_preparacion`, `enviado`, `entregado`, `cancelado`

### 3.8 Envíos

**Calcular costo de envío:**
```http
POST /api/envios/calcular
Content-Type: application/json

{
  "codigo_postal": "1000",
  "provincia": "CABA",
  "metodo_envio": "correo_argentino"
}
```

**Respuesta:**
```json
{
  "costo": 2000,
  "metodo_envio": "correo_argentino",
  "codigo_postal": "1000"
}
```

---

## 🗄️ PASO 4: Estructura de la Base de Datos

### Modelos Principales

1. **Admin:** Administradores del sistema
2. **Categoria:** Categorías de productos (Remeras, Shorts)
3. **Producto:** Productos de la tienda
4. **Talle:** Talles disponibles (XS, S, M, L, XL, XXL)
5. **StockTalle:** Stock por producto y talle
6. **ImagenProducto:** Imágenes de productos
7. **TipoPromocion:** Tipos de promoción (2x1, descuentos, etc.)
8. **PromocionProducto:** Promociones aplicadas a productos
9. **MetodoPago:** Métodos de pago disponibles
10. **Pedido:** Pedidos de clientes
11. **ItemPedido:** Items de cada pedido

### Relaciones

- Un **Producto** pertenece a una **Categoria**
- Un **Producto** tiene múltiples **StockTalle** (uno por cada talle)
- Un **Producto** tiene múltiples **ImagenProducto**
- Un **Producto** puede tener múltiples **PromocionProducto**
- Un **Pedido** tiene múltiples **ItemPedido**
- Cada **ItemPedido** referencia un **Producto** y un **Talle**

---

## 🔧 PASO 5: Funcionalidades del Panel de Administración

### 5.1 Gestión de Stock

**Características:**
- ✅ Ver stock por producto y talle
- ✅ Modificar cantidad de stock manualmente
- ✅ El stock se reduce automáticamente cuando un cliente realiza un pedido
- ✅ Los productos muestran "disponible" o "agotado" según el stock

**Flujo:**
1. Cliente agrega producto al carrito
2. Al crear el pedido, se verifica stock disponible
3. Si hay stock, se reduce automáticamente
4. Si no hay stock, se rechaza el pedido

### 5.2 Gestión de Productos

**Características:**
- ✅ Agregar nuevos productos
- ✅ Eliminar productos
- ✅ Modificar título, descripción, precios
- ✅ Activar/desactivar productos
- ✅ Marcar productos como destacados

### 5.3 Gestión de Imágenes

**Características:**
- ✅ Subir múltiples imágenes por producto
- ✅ Marcar imagen principal
- ✅ Ordenar imágenes
- ✅ Eliminar imágenes

**Formatos soportados:** PNG, JPG, JPEG, GIF, WEBP
**Tamaño máximo:** 16MB por imagen

### 5.4 Gestión de Precios y Promociones

**Características:**
- ✅ Modificar precio base
- ✅ Agregar precio con descuento
- ✅ Crear promociones:
  - Descuento por porcentaje
  - Descuento fijo
  - 2x1 (llevas 2, pagas 1)
  - 3x2 (llevas 3, pagas 2)
  - Llevas X, pagas Y (configurable)
- ✅ Definir fechas de inicio y fin de promociones

**Ejemplo de promoción 2x1:**
- Cliente compra 2 unidades
- Se cobra solo 1 unidad
- El descuento se calcula automáticamente

### 5.5 Gestión de Pedidos

**Características:**
- ✅ Ver todos los pedidos
- ✅ Filtrar por estado
- ✅ Actualizar estado del pedido
- ✅ Agregar notas al pedido
- ✅ Ver detalles completos del pedido

---

## 📦 PASO 6: Integración de Envíos

### Estado Actual

Actualmente, el cálculo de envíos está **simulado** con costos fijos:
- Andreani: $2,500
- Correo Argentino: $2,000
- Tienda Nube: $2,200

### Integración con APIs Reales

Para integrar con servicios reales, necesitas:

#### 6.1 Andreani

1. Registrarse en https://www.andreani.com/
2. Obtener credenciales API
3. Modificar la función `calcular_costo_envio()` en `routes.py`
4. Implementar llamadas a la API de Andreani

#### 6.2 Correo Argentino

1. Registrarse en https://www.correoargentino.com.ar/
2. Obtener credenciales API
3. Implementar integración en `routes.py`

#### 6.3 Tienda Nube

Si tienes cuenta en Tienda Nube, puedes usar su API de envíos.

**Nota:** Estas integraciones requieren credenciales y pueden tener costos asociados. Por ahora, el sistema funciona con la simulación.

---

## 🧪 PASO 7: Pruebas del Backend

### 7.1 Probar Endpoints con Postman o cURL

**Ejemplo: Login**
```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

**Ejemplo: Listar productos**
```bash
curl http://localhost:5000/api/productos
```

**Ejemplo: Crear producto (requiere token)**
```bash
curl -X POST http://localhost:5000/api/admin/productos \
  -H "Authorization: Bearer <tu_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "nombre": "Remera Test",
    "descripcion": "Descripción test",
    "precio_base": 15000,
    "categoria_id": 1,
    "activo": true
  }'
```

### 7.2 Verificar Base de Datos

Puedes usar herramientas como:
- **DB Browser for SQLite** (para SQLite)
- **pgAdmin** (para PostgreSQL)
- O cualquier cliente SQL

---

## 📝 PASO 8: Próximos Pasos

### Backend Completado ✅

- ✅ Estructura del proyecto
- ✅ Modelos de base de datos
- ✅ API REST completa
- ✅ Autenticación JWT
- ✅ Gestión de productos, stock, imágenes
- ✅ Sistema de promociones
- ✅ Gestión de pedidos
- ✅ Cálculo de envíos (simulado)

### Pendiente para el Frontend

1. **Crear proyecto Angular**
2. **Configurar servicios para consumir API**
3. **Crear componentes:**
   - Catálogo de productos
   - Detalle de producto
   - Carrito de compras
   - Checkout
   - Panel de administración
4. **Implementar autenticación en frontend**
5. **Integrar pasarela de pago**

### Mejoras Futuras

- [ ] Integrar APIs reales de envío
- [ ] Implementar pasarela de pago (Mercado Pago)
- [ ] Sistema de notificaciones por email
- [ ] Dashboard con gráficos y estadísticas
- [ ] Sistema de reseñas de productos
- [ ] Búsqueda y filtros avanzados
- [ ] Wishlist (lista de deseos)
- [ ] Sistema de cupones de descuento

---

## 🆘 Solución de Problemas

### Error: "Module not found"

**Solución:** Asegúrate de tener el entorno virtual activado y las dependencias instaladas:
```bash
pip install -r requirements.txt
```

### Error: "Port 5000 already in use"

**Solución:** Cambia el puerto en `app.py`:
```python
app.run(debug=True, host='0.0.0.0', port=5001)
```

### Error: "Database locked"

**Solución:** Cierra otras conexiones a la base de datos o reinicia el servidor.

### Error al subir imágenes

**Solución:** Verifica que la carpeta `static/uploads/` exista y tenga permisos de escritura.

---

## 📚 Recursos Adicionales

- **Documentación Flask:** https://flask.palletsprojects.com/
- **Documentación SQLAlchemy:** https://www.sqlalchemy.org/
- **Documentación Flask-JWT-Extended:** https://flask-jwt-extended.readthedocs.io/

---

## ✅ Checklist de Verificación

Antes de continuar con el frontend, verifica:

- [ ] Backend ejecutándose correctamente
- [ ] Base de datos inicializada con datos de ejemplo
- [ ] Puedes hacer login como admin
- [ ] Puedes listar productos
- [ ] Puedes crear/editar/eliminar productos (como admin)
- [ ] Puedes subir imágenes
- [ ] Puedes gestionar stock
- [ ] Puedes crear promociones
- [ ] Puedes crear pedidos
- [ ] El cálculo de envíos funciona

---

¡El backend está completo y listo para integrarse con el frontend Angular! 🎉
