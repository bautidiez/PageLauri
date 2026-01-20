## INSTRUCCIONES MANUALES PARA ARREGLAR PRODUCTOS-ADMIN

### 1. Categoría Principal (líneas 73-110 aprox)

**REEMPLAZAR TODA LA SECCIÓN DE CATEGORÍAS CON:**

```html
<!-- CATEGORÍA SIMPLIFICADA: Solo Remeras (1) o Shorts (2) -->
<div class="form-group">
  <label>Categoría Principal * (Remeras o Shorts)</label>
  <select [(ngModel)]="nuevoProducto.categoria_id" name="categoria_id" required>
    <option value="">Selecciona Remeras o Shorts</option>
    <option value="1">Remeras</option>
    <option value="2">Shorts</option>
  </select>
</div>
```

### 2. Producto Relacionado con Búsqueda (línea 146-158 aprox)

**REEMPLAZAR EL SELECT CON:**

```html
<!-- Producto Relacionado con BÚSQUEDA ESCRITA -->
<div class="form-group">
  <label>Producto Relacionado (mismo diseño, diferente color)</label>
  <div class="autocomplete-wrapper" style="position: relative;">
    <input 
      type="text" 
      placeholder="Escribe para buscar un producto..."
      [(ngModel)]="busquedaProductoRelacionado"
      (input)="buscarProductoRelacionado()"
      name="product_search"
      style="width: 100%; padding: 12px 40px 12px 12px;"
      autocomplete="off">
    
    <!-- Botón limpiar -->
    <button 
      *ngIf="nuevoProducto.producto_relacionado_id" 
      type="button"
      (click)="limpiarProductoRelacionado()"
      style="position: absolute; right: 10px; top: 50%; transform: translateY(-50%); background: #dc3545; color: #fff; border: none; border-radius: 50%; width: 24px; height: 24px; cursor: pointer;">
      ✕
    </button>
    
    <!-- Lista de sugerencias -->
    <div *ngIf="productosRelacionadosFiltrados.length > 0" 
         style="position: absolute; top: 100%; left: 0; right: 0; background: #fff; border: 2px solid #667eea; border-radius: 8px; margin-top: 4px; max-height: 250px; overflow-y: auto; box-shadow: 0 4px 12px rgba(0,0,0,0.15); z-index: 1000;">
      <div 
        *ngFor="let prod of productosRelacionadosFiltrados"
        (click)="seleccionarProductoRelacionado(prod)"
        style="padding: 12px 15px; cursor: pointer; border-bottom: 1px solid #f0f0f0;"
        (mouseenter)="$event.target.style.background='#f8f9ff'"
        (mouseleave)="$event.target.style.background='#fff'">
        {{ prod.nombre }}
      </div>
    </div>
  </div>
  <small>Escribe para buscar un producto relacionado</small>
</div>
```

### 3. En productos-admin.ts - AGREGAR AL COMIENZO DE LA CLASE:

```typescript
// Búsqueda de producto relacionado
busquedaProductoRelacionado = '';
productosRelacionadosFiltrados: any[] = [];
```

### 4. En productos-admin.ts - AGREGAR MÉTODOS:

```typescript
buscarProductoRelacionado() {
  if (this.busquedaProductoRelacionado.length < 2) {
    this.productosRelacionadosFiltrados = [];
    return;
  }

  const busq = this.busquedaProductoRelacionado.toLowerCase();
  this.productosRelacionadosFiltrados = this.productos.filter(p => 
    p.nombre.toLowerCase().includes(busq) && p.id !== this.nuevoProducto.id
  ).slice(0, 10);
}

seleccionarProductoRelacionado(producto: any) {
  this.nuevoProducto.producto_relacionado_id = producto.id;
  this.busquedaProductoRelacionado = producto.nombre;
  this.productosRelacionadosFiltrados = [];
}

limpiarProductoRelacionado() {
  this.nuevoProducto.producto_relacionado_id = null;
  this.busquedaProductoRelacionado = '';
  this.productosRelacionadosFiltrados = [];
}
```

### 5. ELIMINAR REFERENCIAS A BOTINES Y COLECCIONABLES

**Backend - En PostgreSQL:**
```sql
DELETE FROM categorias WHERE LOWER(nombre) LIKE '%botines%' OR LOWER(nombre) LIKE '%coleccionable%';
```

**Archivos a limpiar:**
- `backend/agregar_categorias.py` - línea 21
- `backend/reorganizar_categorias.py` - línea 39
- `backend/reorganizar_categorias_sqlite.py` - línea 72
- `backend/ejecutar_migraciones.py` - línea 150

En cada uno, eliminar líneas que mencionen "Botines" o "Coleccionables".

---

¡Listo! Con estos cambios quedarán solucionados los 3 problemas.
