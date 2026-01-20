# Backend - El Vestuario

Backend desarrollado con Flask para la tienda online "El Vestuario".

## Características

- ✅ Gestión de productos (60 remeras, 15 shorts)
- ✅ Sistema de stock por talle
- ✅ Panel de administración con autenticación JWT
- ✅ Gestión de imágenes de productos
- ✅ Sistema de promociones (2x1, 3x2, descuentos)
- ✅ Gestión de pedidos
- ✅ Cálculo de envíos (preparado para integración con Andreani, Correo Argentino)
- ✅ Métodos de pago (transferencia, tarjeta débito/crédito)

## Instalación

1. **Crear entorno virtual:**
```bash
python -m venv venv
```

2. **Activar entorno virtual:**
- Windows: `venv\Scripts\activate`
- Linux/Mac: `source venv/bin/activate`

3. **Instalar dependencias:**
```bash
pip install -r requirements.txt
```

4. **Configurar variables de entorno:**
```bash
cp .env.example .env
# Editar .env con tus valores
```

5. **Inicializar base de datos:**
```bash
python init_data.py
```

6. **Ejecutar servidor:**
```bash
python app.py
```

El servidor estará disponible en `http://localhost:5000`

## Credenciales por defecto

- Usuario: `admin`
- Contraseña: `admin123`

**⚠️ IMPORTANTE:** Cambiar estas credenciales en producción.

## Estructura de la API

### Autenticación
- `POST /api/auth/login` - Login de administrador
- `GET /api/auth/verify` - Verificar token (requiere JWT)

### Productos (Público)
- `GET /api/productos` - Listar productos
- `GET /api/productos/<id>` - Obtener producto

### Productos (Admin - requiere JWT)
- `POST /api/admin/productos` - Crear producto
- `PUT /api/admin/productos/<id>` - Actualizar producto
- `DELETE /api/admin/productos/<id>` - Eliminar producto

### Stock (Admin)
- `GET /api/admin/stock` - Listar stock
- `POST /api/admin/stock` - Crear/actualizar stock
- `PUT /api/admin/stock/<id>` - Actualizar stock
- `DELETE /api/admin/stock/<id>` - Eliminar stock

### Imágenes (Admin)
- `POST /api/admin/productos/<id>/imagenes` - Subir imagen
- `DELETE /api/admin/imagenes/<id>` - Eliminar imagen

### Promociones
- `GET /api/promociones` - Listar promociones activas
- `POST /api/admin/promociones` - Crear promoción (admin)
- `PUT /api/admin/promociones/<id>` - Actualizar promoción (admin)
- `DELETE /api/admin/promociones/<id>` - Eliminar promoción (admin)

### Pedidos
- `POST /api/pedidos` - Crear pedido (público)
- `GET /api/admin/pedidos` - Listar pedidos (admin)
- `GET /api/admin/pedidos/<id>` - Obtener pedido (admin)
- `PUT /api/admin/pedidos/<id>` - Actualizar pedido (admin)

### Envíos
- `POST /api/envios/calcular` - Calcular costo de envío

## Integración con servicios de envío

Actualmente el cálculo de envíos está simulado. Para integrar con servicios reales:

1. **Andreani:** Registrar en https://www.andreani.com/ y obtener credenciales API
2. **Correo Argentino:** Registrar en https://www.correoargentino.com.ar/ y obtener credenciales API
3. **Tienda Nube:** Si tienes cuenta, usar su API de envíos

Modificar la función `calcular_costo_envio()` en `routes.py` para integrar las APIs reales.

## Base de datos

Por defecto usa SQLite (`elvestuario.db`). Para producción, se recomienda PostgreSQL:

```python
DATABASE_URL=postgresql://usuario:password@localhost/elvestuario
```

## Próximos pasos

- [ ] Integrar APIs reales de envío
- [ ] Implementar pasarela de pago (Mercado Pago, etc.)
- [ ] Agregar sistema de notificaciones por email
- [ ] Implementar caché para mejorar rendimiento
- [ ] Agregar logs y monitoreo
