# Panel de Administrador - El Vestuario

## 📋 Resumen

El panel de administrador está **completamente implementado en el backend** con todas las funcionalidades solicitadas. El backend proporciona una API REST completa que el frontend Angular consumirá para crear la interfaz visual del panel.

## 🔐 Autenticación

### Login de Administrador
- **Endpoint:** `POST /api/auth/login`
- **Descripción:** Permite al administrador iniciar sesión
- **Credenciales por defecto:**
  - Usuario: `admin`
  - Contraseña: `admin123`
- **Respuesta:** Devuelve un token JWT que se usa para acceder a todas las funcionalidades del panel

### Verificación de Token
- **Endpoint:** `GET /api/auth/verify`
- **Descripción:** Verifica si el token del administrador es válido
- **Uso:** Para mantener la sesión activa en el frontend

---

## 📦 Gestión de Productos

### 1. Crear Producto
- **Endpoint:** `POST /api/admin/productos`
- **Funcionalidad:** Agregar nuevos productos al catálogo
- **Datos que se pueden configurar:**
  - ✅ Nombre del producto
  - ✅ Descripción
  - ✅ Precio base
  - ✅ Precio con descuento (opcional)
  - ✅ Categoría (Remeras o Shorts)
  - ✅ Estado (activo/inactivo)
  - ✅ Destacado (sí/no)
  - ✅ Stock inicial por talle

### 2. Modificar Producto
- **Endpoint:** `PUT /api/admin/productos/<id>`
- **Funcionalidad:** Editar cualquier campo del producto
- **Puede modificar:**
  - ✅ Título (nombre)
  - ✅ Descripción
  - ✅ Precio base
  - ✅ Precio con descuento
  - ✅ Categoría
  - ✅ Estado activo/inactivo
  - ✅ Marcar como destacado

### 3. Eliminar Producto
- **Endpoint:** `DELETE /api/admin/productos/<id>`
- **Funcionalidad:** Eliminar productos del catálogo
- **Nota:** También elimina automáticamente todas las imágenes asociadas

### 4. Listar Productos
- **Endpoint:** `GET /api/admin/productos` (público también disponible)
- **Funcionalidad:** Ver todos los productos con sus detalles completos

---

## 📸 Gestión de Imágenes

### 1. Subir Imágenes
- **Endpoint:** `POST /api/admin/productos/<id>/imagenes`
- **Funcionalidad:** Agregar imágenes a los productos
- **Características:**
  - ✅ Múltiples imágenes por producto
  - ✅ Marcar imagen principal
  - ✅ Ordenar imágenes
  - ✅ Formatos soportados: PNG, JPG, JPEG, GIF, WEBP
  - ✅ Tamaño máximo: 16MB por imagen

### 2. Eliminar Imágenes
- **Endpoint:** `DELETE /api/admin/imagenes/<id>`
- **Funcionalidad:** Eliminar imágenes de productos
- **Nota:** También elimina el archivo físico del servidor

---

## 📊 Gestión de Stock

### 1. Ver Stock
- **Endpoint:** `GET /api/admin/stock`
- **Funcionalidad:** Ver el stock de todos los productos
- **Filtros disponibles:**
  - Por producto específico
  - Ver stock por talle

### 2. Modificar Stock
- **Endpoint:** `PUT /api/admin/stock/<id>`
- **Funcionalidad:** Cambiar la cantidad de stock manualmente
- **Características:**
  - ✅ El admin puede modificar cualquier cantidad
  - ✅ Se actualiza automáticamente cuando un cliente compra
  - ✅ Muestra "disponible" o "agotado" según el stock

### 3. Crear/Actualizar Stock
- **Endpoint:** `POST /api/admin/stock`
- **Funcionalidad:** Agregar stock para un producto-talle específico
- **Uso:** Cuando se agrega un nuevo talle a un producto o se repone stock

### 4. Eliminar Stock
- **Endpoint:** `DELETE /api/admin/stock/<id>`
- **Funcionalidad:** Eliminar registro de stock (útil para eliminar talles de productos)

### 5. Reducción Automática de Stock
- **Funcionalidad:** Cuando un cliente realiza un pedido, el stock se reduce automáticamente
- **Validación:** Si no hay stock suficiente, el pedido se rechaza
- **Aplicación:** Funciona por talle (cada talle tiene su propio stock)

---

## 🏷️ Gestión de Talles

### 1. Ver Talles
- **Endpoint:** `GET /api/talles` (público)
- **Funcionalidad:** Listar todos los talles disponibles
- **Talles por defecto:** XS, S, M, L, XL, XXL

### 2. Crear Talle
- **Endpoint:** `POST /api/admin/talles`
- **Funcionalidad:** Agregar nuevos talles al sistema

### 3. Eliminar Talle
- **Endpoint:** `DELETE /api/admin/talles/<id>`
- **Funcionalidad:** Eliminar talles del sistema

---

## 🎯 Gestión de Precios y Descuentos

### 1. Modificar Precios
- **Funcionalidad:** Incluida en la edición de productos
- **Puede modificar:**
  - ✅ Precio base
  - ✅ Precio con descuento
  - ✅ El sistema calcula automáticamente el precio actual

### 2. Agregar Descuentos
- **Método 1:** Precio con descuento directo
  - Se establece un `precio_descuento` en el producto
  - El sistema muestra el precio rebajado automáticamente

- **Método 2:** Descuento por porcentaje (vía promociones)
- **Método 3:** Descuento fijo en pesos (vía promociones)

---

## 🎁 Gestión de Promociones

### 1. Crear Promoción
- **Endpoint:** `POST /api/admin/promociones`
- **Funcionalidad:** Crear promociones especiales para productos
- **Tipos de promoción disponibles:**
  - ✅ **2x1:** Llevas 2, pagas 1
  - ✅ **3x2:** Llevas 3, pagas 2
  - ✅ **Llevas 3, pagas 2:** Variante de 3x2
  - ✅ **Descuento por porcentaje:** Ej: 20% de descuento
  - ✅ **Descuento fijo:** Ej: $2000 de descuento

### 2. Configurar Promociones
- **Datos configurables:**
  - ✅ Producto al que aplica
  - ✅ Tipo de promoción
  - ✅ Valor (porcentaje o monto)
  - ✅ Fecha de inicio
  - ✅ Fecha de fin
  - ✅ Activar/desactivar

### 3. Modificar Promoción
- **Endpoint:** `PUT /api/admin/promociones/<id>`
- **Funcionalidad:** Editar cualquier aspecto de la promoción

### 4. Eliminar Promoción
- **Endpoint:** `DELETE /api/admin/promociones/<id>`
- **Funcionalidad:** Eliminar promociones

### 5. Ver Promociones Activas
- **Endpoint:** `GET /api/promociones`
- **Funcionalidad:** Listar promociones activas (público)
- **Filtros:** Por producto específico

### 6. Cálculo Automático
- **Funcionalidad:** El sistema calcula automáticamente los descuentos al crear un pedido
- **Ejemplo:** Si hay promoción 2x1 y el cliente compra 4 unidades, se cobran solo 2

---

## 📦 Gestión de Pedidos

### 1. Ver Todos los Pedidos
- **Endpoint:** `GET /api/admin/pedidos`
- **Funcionalidad:** Listar todos los pedidos del sistema
- **Filtros:** Por estado (pendiente, confirmado, en_preparacion, enviado, entregado, cancelado)

### 2. Ver Detalle de Pedido
- **Endpoint:** `GET /api/admin/pedidos/<id>`
- **Funcionalidad:** Ver información completa de un pedido
- **Información incluida:**
  - ✅ Datos del cliente
  - ✅ Productos comprados
  - ✅ Talles y cantidades
  - ✅ Precios y descuentos aplicados
  - ✅ Método de pago
  - ✅ Método de envío
  - ✅ Costo de envío
  - ✅ Total del pedido
  - ✅ Estado actual
  - ✅ Notas

### 3. Actualizar Estado de Pedido
- **Endpoint:** `PUT /api/admin/pedidos/<id>`
- **Funcionalidad:** Cambiar el estado del pedido
- **Estados disponibles:**
  - `pendiente` - Pedido recién creado
  - `confirmado` - Pedido confirmado por el admin
  - `en_preparacion` - Pedido siendo preparado
  - `enviado` - Pedido enviado al cliente
  - `entregado` - Pedido entregado
  - `cancelado` - Pedido cancelado

### 4. Agregar Notas
- **Funcionalidad:** Incluida en la actualización de pedidos
- **Uso:** Para agregar comentarios o instrucciones especiales

---

## 📈 Estadísticas del Sistema

### 1. Ver Estadísticas
- **Endpoint:** `GET /api/admin/estadisticas`
- **Funcionalidad:** Obtener estadísticas generales del sistema
- **Información proporcionada:**
  - ✅ Total de productos
  - ✅ Productos activos
  - ✅ Productos sin stock
  - ✅ Total de pedidos
  - ✅ Pedidos pendientes
  - ✅ Total de ventas (pedidos entregados)

---

## 🏷️ Gestión de Categorías

### 1. Crear Categoría
- **Endpoint:** `POST /api/admin/categorias`
- **Funcionalidad:** Agregar nuevas categorías
- **Categorías por defecto:** Remeras, Shorts

### 2. Modificar Categoría
- **Endpoint:** `PUT /api/admin/categorias/<id>`
- **Funcionalidad:** Editar nombre y descripción de categorías
- **Puede:** Activar/desactivar categorías

---

## 🚚 Gestión de Envíos

### 1. Calcular Costo de Envío
- **Endpoint:** `POST /api/envios/calcular` (público)
- **Funcionalidad:** Calcular costo de envío según destino
- **Métodos de envío disponibles:**
  - ✅ Andreani
  - ✅ Correo Argentino
  - ✅ Tienda Nube
- **Estado actual:** Simulado (preparado para integración con APIs reales)

### 2. Integración con Servicios de Envío
- **Preparado para:**
  - Andreani API
  - Correo Argentino API
  - Tienda Nube API
- **Nota:** Actualmente usa costos simulados, pero la estructura está lista para integrar APIs reales

---

## 💳 Métodos de Pago

### 1. Ver Métodos de Pago
- **Endpoint:** `GET /api/metodos-pago` (público)
- **Funcionalidad:** Listar métodos de pago disponibles
- **Métodos por defecto:**
  - ✅ Transferencia bancaria
  - ✅ Tarjeta de débito
  - ✅ Tarjeta de crédito

---

## ✅ Checklist de Funcionalidades Implementadas

### Gestión de Productos
- [x] Agregar productos
- [x] Eliminar productos
- [x] Modificar título y descripción
- [x] Modificar precios
- [x] Agregar imágenes
- [x] Eliminar imágenes
- [x] Marcar imagen principal
- [x] Ordenar imágenes

### Gestión de Stock
- [x] Ver stock por producto y talle
- [x] Modificar cantidad de stock manualmente
- [x] Reducción automática al comprar
- [x] Indicador disponible/agotado
- [x] Gestión de talles

### Gestión de Precios y Promociones
- [x] Modificar precios
- [x] Agregar descuentos
- [x] Crear promociones 2x1
- [x] Crear promociones "llevas 3, pagas 2"
- [x] Descuentos por porcentaje
- [x] Descuentos fijos
- [x] Fechas de inicio y fin de promociones

### Gestión de Pedidos
- [x] Ver todos los pedidos
- [x] Ver detalle de pedidos
- [x] Actualizar estado de pedidos
- [x] Agregar notas a pedidos

### Otros
- [x] Autenticación JWT
- [x] Estadísticas del sistema
- [x] Gestión de categorías
- [x] Cálculo de envíos (simulado)
- [x] Métodos de pago

---

## 🎯 Resumen de Endpoints del Panel

### Autenticación
- `POST /api/auth/login` - Login
- `GET /api/auth/verify` - Verificar token

### Productos (Admin)
- `GET /api/admin/productos` - Listar productos
- `POST /api/admin/productos` - Crear producto
- `PUT /api/admin/productos/<id>` - Modificar producto
- `DELETE /api/admin/productos/<id>` - Eliminar producto

### Imágenes (Admin)
- `POST /api/admin/productos/<id>/imagenes` - Subir imagen
- `DELETE /api/admin/imagenes/<id>` - Eliminar imagen

### Stock (Admin)
- `GET /api/admin/stock` - Listar stock
- `POST /api/admin/stock` - Crear/actualizar stock
- `PUT /api/admin/stock/<id>` - Modificar stock
- `DELETE /api/admin/stock/<id>` - Eliminar stock

### Talles (Admin)
- `POST /api/admin/talles` - Crear talle
- `DELETE /api/admin/talles/<id>` - Eliminar talle

### Promociones (Admin)
- `GET /api/admin/tipos-promocion` - Listar tipos de promoción
- `POST /api/admin/promociones` - Crear promoción
- `PUT /api/admin/promociones/<id>` - Modificar promoción
- `DELETE /api/admin/promociones/<id>` - Eliminar promoción

### Pedidos (Admin)
- `GET /api/admin/pedidos` - Listar pedidos
- `GET /api/admin/pedidos/<id>` - Ver pedido
- `PUT /api/admin/pedidos/<id>` - Actualizar pedido

### Categorías (Admin)
- `POST /api/admin/categorias` - Crear categoría
- `PUT /api/admin/categorias/<id>` - Modificar categoría

### Estadísticas (Admin)
- `GET /api/admin/estadisticas` - Ver estadísticas

---

## 📝 Notas Importantes

1. **Todas las funcionalidades están implementadas en el backend**
2. **El frontend Angular consumirá estos endpoints para crear la interfaz visual**
3. **Todas las rutas de administrador requieren autenticación JWT**
4. **El stock se reduce automáticamente cuando se crea un pedido**
5. **Las promociones se calculan automáticamente en los pedidos**
6. **Las imágenes se almacenan en `backend/static/uploads/`**

---

## 🚀 Próximos Pasos

El backend del panel de administrador está **100% completo**. El siguiente paso es:

1. **Desarrollar el frontend Angular** que consuma estos endpoints
2. **Crear la interfaz visual** del panel de administración
3. **Implementar las integraciones reales** de envío (Andreani, Correo Argentino)

---

¡El panel de administrador está completamente funcional en el backend! 🎉
