# Frontend - El Vestuario

Frontend desarrollado con Angular para la tienda online "El Vestuario".

## 🚀 Instalación y Ejecución

### Prerrequisitos
- Node.js 18+ instalado
- npm o yarn

### Pasos

1. **Instalar dependencias:**
```bash
cd frontend
npm install
```

2. **Ejecutar servidor de desarrollo:**
```bash
npm start
```

El frontend estará disponible en `http://localhost:4200`

### ⚠️ Importante
Asegúrate de que el backend Flask esté corriendo en `http://localhost:5000`

## 📁 Estructura del Proyecto

```
frontend/
├── src/
│   ├── app/
│   │   ├── components/          # Componentes reutilizables
│   │   │   ├── header/          # Header con navegación
│   │   │   └── footer/          # Footer
│   │   ├── pages/               # Páginas principales
│   │   │   ├── home/           # Página de inicio
│   │   │   ├── productos/      # Catálogo de productos
│   │   │   ├── producto-detail/ # Detalle de producto
│   │   │   ├── cart/           # Carrito de compras
│   │   │   ├── checkout/        # Proceso de compra
│   │   │   └── admin/          # Panel de administración
│   │   │       ├── login/      # Login admin
│   │   │       └── dashboard/  # Dashboard admin
│   │   └── services/           # Servicios
│   │       ├── api.service.ts   # Servicio API
│   │       ├── auth.service.ts # Servicio autenticación
│   │       └── cart.service.ts # Servicio carrito
│   └── environments/            # Variables de entorno
└── package.json
```

## 🎨 Características Implementadas

### Páginas Públicas
- ✅ Página de inicio con productos destacados
- ✅ Catálogo de productos con filtros
- ✅ Detalle de producto con selección de talle
- ✅ Carrito de compras
- ✅ Checkout (en desarrollo)
- ✅ Header y Footer responsive

### Panel de Administración
- ✅ Login de administrador
- ✅ Dashboard (en desarrollo)
- ✅ Gestión de productos
- ✅ Gestión de stock
- ✅ Gestión de promociones
- ✅ Gestión de pedidos

## 🔧 Servicios

### ApiService
Maneja todas las llamadas HTTP al backend Flask.

### AuthService
Gestiona la autenticación del administrador con JWT.

### CartService
Maneja el carrito de compras del cliente.

## 🎯 Próximos Pasos

- [ ] Completar componente de checkout
- [ ] Completar panel de administración
- [ ] Agregar gestión de imágenes
- [ ] Implementar búsqueda de productos
- [ ] Agregar paginación
- [ ] Mejorar diseño responsive

## 📝 Notas

- El diseño está inspirado en Torero Deportes
- Todos los componentes son responsive
- El carrito se guarda en localStorage
- La autenticación usa JWT tokens
