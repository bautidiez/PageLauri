# 🚀 Instrucciones para Ejecutar el Proyecto

## 📋 Requisitos Previos

1. **Python 3.8+** instalado
2. **Node.js 18+** y npm instalados
3. **Git** (opcional, para clonar el repositorio)

---

## 🔧 Configuración Inicial (Solo la primera vez)

### 1. Configurar Backend

```powershell
# Navegar a la carpeta backend
cd backend

# Activar entorno virtual (si ya existe)
.\venv\Scripts\Activate.ps1

# Si no existe el entorno virtual, crearlo:
python -m venv venv
.\venv\Scripts\Activate.ps1

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar migraciones (si es necesario)
python migrar_colores_stock.py
```

### 2. Configurar Frontend

```powershell
# Navegar a la carpeta frontend
cd frontend

# Instalar dependencias (solo la primera vez)
npm install
```

---

## ▶️ Ejecutar el Proyecto

### Opción 1: Usando Scripts .bat (Recomendado)

#### **Paso 1: Iniciar Backend**

Doble clic en: `INICIAR_BACKEND.bat`

O desde PowerShell:
```powershell
.\INICIAR_BACKEND.bat
```

El backend estará disponible en: **http://localhost:5000**

#### **Paso 2: Iniciar Frontend**

Doble clic en: `INICIAR_FRONTEND.bat`

O desde PowerShell:
```powershell
.\INICIAR_FRONTEND.bat
```

El frontend estará disponible en: **http://localhost:4200**

---

### Opción 2: Manualmente

#### **Terminal 1 - Backend:**

```powershell
cd backend
.\venv\Scripts\Activate.ps1
python app.py
```

#### **Terminal 2 - Frontend:**

```powershell
cd frontend
npm start
```

---

## 🌐 Acceder a la Aplicación

Una vez que ambos servidores estén corriendo:

- **Frontend (Cliente):** http://localhost:4200
- **Backend (API):** http://localhost:5000
- **Panel Admin:** http://localhost:4200/admin/login

---

## 🔐 Credenciales por Defecto

Si es la primera vez que ejecutas el proyecto, el sistema creará automáticamente un usuario admin:

- **Usuario:** admin
- **Contraseña:** admin

**⚠️ IMPORTANTE:** Cambia estas credenciales en producción.

---

## 📁 Estructura de Archivos Importantes

```
PagLauri/
├── backend/
│   ├── app.py              # Servidor Flask
│   ├── models.py           # Modelos de base de datos
│   ├── routes.py           # Rutas API
│   ├── elvestuario.db      # Base de datos SQLite
│   └── venv/               # Entorno virtual Python
│
├── frontend/
│   ├── src/                # Código fuente Angular
│   ├── package.json        # Dependencias Node.js
│   └── node_modules/       # Dependencias instaladas
│
├── INICIAR_BACKEND.bat     # Script para iniciar backend
└── INICIAR_FRONTEND.bat    # Script para iniciar frontend
```

---

## 🛠️ Solución de Problemas

### Error: "Puerto 5000 ya está en uso"
```powershell
# Encontrar y cerrar el proceso
netstat -ano | findstr :5000
taskkill /PID <PID_NUMBER> /F
```

### Error: "Puerto 4200 ya está en uso"
```powershell
# Encontrar y cerrar el proceso
netstat -ano | findstr :4200
taskkill /PID <PID_NUMBER> /F
```

### Error: "No se encuentra el módulo"
```powershell
# Backend
cd backend
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Frontend
cd frontend
npm install
```

### Error: "Base de datos no encontrada"
```powershell
cd backend
.\venv\Scripts\Activate.ps1
python -c "from app import app, db; app.app_context().push(); db.create_all()"
python migrar_colores_stock.py
```

---

## 📝 Notas Importantes

1. **Siempre ejecuta primero el Backend** antes del Frontend
2. **Mantén ambas terminales abiertas** mientras trabajas
3. **Para detener los servidores:** Presiona `Ctrl+C` en cada terminal
4. **Los cambios en el código se reflejan automáticamente** (hot reload)

---

## ✅ Verificación

Una vez iniciado, deberías ver:

**Backend:**
```
 * Running on http://127.0.0.1:5000
```

**Frontend:**
```
✔ Compiled successfully.
** Angular Live Development Server is listening on localhost:4200 **
```

---

## 🎯 Próximos Pasos

1. Accede a http://localhost:4200
2. Inicia sesión en el panel admin: http://localhost:4200/admin/login
3. Crea categorías, productos y gestiona el stock
4. ¡Disfruta de tu tienda!

---

¿Necesitas ayuda? Revisa los logs en las terminales para más información.
