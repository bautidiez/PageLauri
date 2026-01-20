# 🚀 Guía Completa de Ejecución - El Vestuario

## 📋 Requisitos Previos

- **Python 3.8+** instalado
- **Node.js 18+** y npm instalados
- **Git** (opcional, para clonar el repositorio)

---

## 🔧 Configuración Inicial

### 1. Verificar Estructura del Proyecto

Asegúrate de tener esta estructura:
```
PagLauri/
├── backend/
│   ├── app.py
│   ├── models.py
│   ├── routes.py
│   ├── requirements.txt
│   ├── .env
│   ├── venv/ (entorno virtual)
│   └── elvestuario.db (se crea automáticamente)
└── frontend/
    ├── src/
    ├── package.json
    └── node_modules/ (se instala con npm)
```

---

## 🐍 BACKEND - Configuración y Ejecución

### Paso 1: Navegar al directorio backend

```powershell
cd C:\Bau\PagLauri\backend
```

### Paso 2: Crear y activar el entorno virtual (si no existe)

```powershell
# Crear entorno virtual
python -m venv venv

# Activar entorno virtual (Windows PowerShell)
.\venv\Scripts\Activate.ps1

# Si tienes problemas con la política de ejecución, ejecuta primero:
# Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Paso 3: Instalar dependencias

```powershell
pip install -r requirements.txt
```

### Paso 4: Configurar variables de entorno

Crea o verifica el archivo `.env` en la carpeta `backend/`:

```env
SECRET_KEY=tu-clave-secreta-super-segura-aqui
JWT_SECRET_KEY=tu-jwt-secret-key-super-segura-aqui
DATABASE_URL=sqlite:///elvestuario.db
```

### Paso 5: Ejecutar migraciones de base de datos

```powershell
# Asegúrate de que el entorno virtual esté activado
.\venv\Scripts\Activate.ps1

# Ejecutar migración de columnas (agregar nuevos campos)
python migrar_columnas.py

# Agregar nuevas categorías
python agregar_categorias.py

# Inicializar datos base (talles, métodos de pago, etc.)
python init_data.py
```

### Paso 6: Iniciar el servidor Flask

```powershell
# Asegúrate de que el entorno virtual esté activado
.\venv\Scripts\Activate.ps1

# Iniciar servidor
python app.py
```

El servidor se iniciará en: **http://localhost:5000**

**Credenciales de administrador por defecto:**
- Usuario: `admin`
- Contraseña: `admin123`

---

## ⚛️ FRONTEND - Configuración y Ejecución

### Paso 1: Navegar al directorio frontend

Abre una **nueva terminal** (mantén el backend corriendo en otra):

```powershell
cd C:\Bau\PagLauri\frontend
```

### Paso 2: Instalar dependencias (solo la primera vez)

```powershell
npm install
```

### Paso 3: Verificar configuración

Abre `frontend/src/environments/environment.ts` y verifica:

```typescript
export const environment = {
  production: false,
  apiUrl: 'http://localhost:5000/api'
};
```

### Paso 4: Compilar y ejecutar en modo desarrollo

```powershell
# Opción 1: Servidor de desarrollo (recomendado)
ng serve

# Opción 2: Compilar para producción
npm run build
```

El frontend se iniciará en: **http://localhost:4200**

---

## 🎯 Ejecución Completa (Backend + Frontend)

### Terminal 1 - Backend:

```powershell
cd C:\Bau\PagLauri\backend
.\venv\Scripts\Activate.ps1
python app.py
```

**Deberías ver:**
```
 * Running on http://0.0.0.0:5000
 * Debug mode: on
```

### Terminal 2 - Frontend:

```powershell
cd C:\Bau\PagLauri\frontend
ng serve
```

**Deberías ver:**
```
✔ Compiled successfully.
** Angular Live Development Server is listening on localhost:4200 **
```

### Acceder a la aplicación:

- **Frontend (Tienda)**: http://localhost:4200
- **Backend API**: http://localhost:5000/api
- **Panel Admin**: http://localhost:4200/admin/login

---

## ✅ Verificación de Funcionalidades

### 1. Verificar Backend

Abre en el navegador o usa curl:

```powershell
# Probar endpoint de productos
curl http://localhost:5000/api/productos

# Probar endpoint de categorías
curl http://localhost:5000/api/categorias
```

### 2. Verificar Frontend

1. Abre http://localhost:4200
2. Verifica que la página carga correctamente
3. Prueba el buscador en el header
4. Navega a "Productos" y prueba los filtros
5. Prueba el ordenamiento de productos

### 3. Verificar Panel Admin

1. Ve a http://localhost:4200/admin/login
2. Inicia sesión con:
   - Usuario: `admin`
   - Contraseña: `admin123`
3. Verifica que puedas acceder al Panel Principal
4. Prueba el Panel de Gestión
5. Verifica las estadísticas de ventas

---

## 🔍 Solución de Problemas Comunes

### Error: "ModuleNotFoundError: No module named 'flask'"

**Solución:**
```powershell
# Asegúrate de que el entorno virtual esté activado
cd C:\Bau\PagLauri\backend
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Error: "Cannot find module '@angular/core'"

**Solución:**
```powershell
cd C:\Bau\PagLauri\frontend
npm install
```

### Error: "Port 5000 already in use"

**Solución:**
- Cierra otros procesos que usen el puerto 5000
- O cambia el puerto en `backend/app.py`:
  ```python
  app.run(debug=True, host='0.0.0.0', port=5001)
  ```

### Error: "Port 4200 already in use"

**Solución:**
```powershell
# Usar otro puerto
ng serve --port 4201
```

### Error: "no such column: productos.color"

**Solución:**
```powershell
cd C:\Bau\PagLauri\backend
.\venv\Scripts\Activate.ps1
python migrar_columnas.py
```

### Error: "Policy execution" en PowerShell

**Solución:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

---

## 📝 Comandos Rápidos de Referencia

### Backend:

```powershell
# Activar entorno virtual
cd C:\Bau\PagLauri\backend
.\venv\Scripts\Activate.ps1

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar migraciones
python migrar_columnas.py
python agregar_categorias.py
python init_data.py

# Iniciar servidor
python app.py
```

### Frontend:

```powershell
# Instalar dependencias
cd C:\Bau\PagLauri\frontend
npm install

# Servidor de desarrollo
ng serve

# Compilar para producción
npm run build

# Ejecutar en otro puerto
ng serve --port 4201
```

---

## 🎨 Funcionalidades Implementadas

### ✅ Buscador de Productos
- Buscador en el header
- Búsqueda por nombre o descripción
- Integrado con filtros

### ✅ Categorías
- 12 categorías disponibles
- Filtrado por categoría
- Navegación por categorías

### ✅ Ordenamiento
- Más vendido
- Orden alfabético
- Precio: Menor a Mayor
- Precio: Mayor a Menor
- Destacado

### ✅ Filtros Avanzados
- Por categoría
- Por color
- Por talle
- Por dorsal
- Por número
- Por versión (Hincha/Jugador)
- Por rango de precio
- Solo destacados

### ✅ Panel de Administración
- Panel Principal con estadísticas
- Panel de Gestión
- Gestión de productos
- Gestión de stock
- Gestión de pedidos
- Gestión de promociones
- Estadísticas avanzadas de ventas

---

## 📞 Soporte

Si encuentras algún problema:

1. Verifica que todos los pasos se hayan ejecutado correctamente
2. Revisa los logs de error en las terminales
3. Asegúrate de que ambos servidores (backend y frontend) estén corriendo
4. Verifica que las URLs en `environment.ts` sean correctas

---

## 🎉 ¡Listo para usar!

Una vez que ambos servidores estén corriendo, puedes:

1. **Navegar la tienda** en http://localhost:4200
2. **Buscar productos** usando el buscador
3. **Filtrar productos** por categoría, color, talle, etc.
4. **Ordenar productos** por diferentes criterios
5. **Gestionar la tienda** desde el panel de administración

¡Disfruta de tu tienda El Vestuario! 🚀
