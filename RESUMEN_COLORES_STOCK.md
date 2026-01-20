# ✅ Sistema de Colores y Stock por Color

## 🎯 Cambios Implementados

### 1. ✅ Modelo Color Creado

**Nuevo modelo:**
- Tabla `colores` con campos:
  - `id`: Identificador único
  - `nombre`: Nombre del color (ej: "Negro Y Plata", "Rojo Y Plata")
  - `codigo_hex`: Código hexadecimal opcional del color
  - `created_at`: Fecha de creación

**Archivos modificados:**
- `backend/models.py` - Modelo Color agregado

---

### 2. ✅ StockTalle Modificado

**Cambios:**
- Agregado campo `color_id` (nullable) a `stock_talles`
- Stock ahora es: **Producto + Color + Talle**
- Constraint único: `(producto_id, color_id, talle_id)`
- Permite productos sin color específico (color_id = NULL)

**Archivos modificados:**
- `backend/models.py` - StockTalle actualizado

---

### 3. ✅ Rutas de API para Colores

**Endpoints creados:**
- `GET /api/colores` - Obtener todos los colores (público)
- `POST /api/admin/colores` - Crear color (admin)
- `PUT /api/admin/colores/<id>` - Actualizar color (admin)
- `DELETE /api/admin/colores/<id>` - Eliminar color (admin)

**Endpoint de stock actualizado:**
- `POST /api/admin/stock` - Ahora acepta `color_id` opcional

**Archivos modificados:**
- `backend/routes.py` - Rutas de colores agregadas

---

### 4. ✅ Frontend - Gestión de Stock

**Cambios en stock-admin:**
- Campo de selección de color agregado al formulario
- Tabla muestra colores en stock
- Badge visual para colores
- Soporte para productos sin color específico

**Archivos modificados:**
- `frontend/src/app/pages/admin/stock-admin/stock-admin.ts`
- `frontend/src/app/pages/admin/stock-admin/stock-admin.html`
- `frontend/src/app/pages/admin/stock-admin/stock-admin.css`
- `frontend/src/app/services/api.service.ts` - Métodos de colores agregados

---

### 5. ✅ Script de Migración

**Script creado:**
- `backend/migrar_colores_stock.py`
- Crea tabla `colores`
- Agrega columna `color_id` a `stock_talles`
- Crea índices únicos
- Agrega colores comunes por defecto

---

## 🚀 Cómo Usar

### 1. Ejecutar Migración

```powershell
cd backend
.\venv\Scripts\Activate.ps1
python migrar_colores_stock.py
```

### 2. Agregar Stock con Color

1. Ve a **Panel de Gestión > Gestión de Stock**
2. Click en **"+ Nuevo Stock"**
3. Selecciona:
   - **Producto**
   - **Color** (opcional - puede dejar "Sin color específico")
   - **Talle**
   - **Cantidad**
4. Click en **Guardar**

### 3. Ejemplo de Uso

**Producto: Remera Boca Juniors**
- Color: Negro Y Plata, Talle: M, Cantidad: 10
- Color: Negro Y Plata, Talle: L, Cantidad: 15
- Color: Rojo Y Plata, Talle: M, Cantidad: 8
- Color: Rojo Y Plata, Talle: L, Cantidad: 12

Cada combinación (Producto + Color + Talle) tiene su propio stock independiente.

---

## 📋 Estructura de Datos

### StockTalle:
```
- producto_id (FK)
- color_id (FK, nullable) ← NUEVO
- talle_id (FK)
- cantidad
```

### Constraint Único:
```
(producto_id, color_id, talle_id) debe ser único
```

---

## ✅ Estado

- ✅ Modelo Color creado
- ✅ StockTalle modificado
- ✅ Rutas de API creadas
- ✅ Frontend actualizado
- ✅ Script de migración creado
- ✅ Compilación exitosa

**Todo listo para usar!** 🎉

---

## ⚠️ Notas Importantes

1. **Compatibilidad:** Los productos existentes sin color seguirán funcionando (color_id = NULL)
2. **Migración:** Ejecutar `migrar_colores_stock.py` antes de usar
3. **Colores por defecto:** El script agrega colores comunes automáticamente
4. **Eliminación:** No se puede eliminar un color que tiene stock asociado
