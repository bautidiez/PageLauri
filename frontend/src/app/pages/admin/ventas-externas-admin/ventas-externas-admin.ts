import { Component, OnInit, OnDestroy, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, RouterModule } from '@angular/router';
import { ApiService } from '../../../services/api.service';
import { AuthService } from '../../../services/auth.service';
import { Subject } from 'rxjs';
import { takeUntil, debounceTime, distinctUntilChanged, switchMap } from 'rxjs/operators';

interface VentaExterna {
    id: number;
    producto_id: number;
    producto_nombre: string;
    talle_id: number;
    talle_nombre: string;
    cantidad: number;
    precio_unitario: number;
    ganancia_total: number;
    fecha: string;
    admin_id: number;
    admin_username: string;
    notas: string;
    created_at: string;
}

interface Producto {
    id: number;
    nombre: string;
    precio_base: number;
    precio_descuento?: number;
    precio_actual: number;
}

interface Talle {
    id: number;
    nombre: string;
}

interface StockTalle {
    producto_id: number;
    talle_id: number;
    cantidad: number;
}

@Component({
    selector: 'app-ventas-externas-admin',
    standalone: true,
    imports: [CommonModule, FormsModule, RouterModule],
    templateUrl: './ventas-externas-admin.html',
    styleUrls: ['./ventas-externas-admin.css']
})
export class VentasExternasAdminComponent implements OnInit, OnDestroy {
    private destroy$ = new Subject<void>();

    // Listas
    ventas: VentaExterna[] = [];
    productos: Producto[] = [];
    talles: Talle[] = [];
    stockDisponible: StockTalle[] = [];

    // Paginación
    currentPage = 1;
    pageSize = 50;
    totalVentas = 0;
    totalPages = 0;

    // Formulario
    nuevaVenta = {
        producto_id: null as number | null,
        talle_id: null as number | null,
        cantidad: 1,
        precio_unitario: 0,
        notas: ''
    };

    // Filtros
    filtroProductoId: number | null = null;
    filtroFechaDesde: string = '';
    filtroFechaHasta: string = '';

    // Estados
    loading = true;
    loadingVentas = false;
    submitting = false;
    error = '';
    success = '';

    // Producto seleccionado para mostrar stock
    productoSeleccionado: Producto | null = null;
    stockProductoSeleccionado: StockTalle[] = [];

    // Búsqueda de productos
    searchQuery = '';
    searchResults: Producto[] = [];
    searching = false;
    private searchSubject = new Subject<string>();

    constructor(
        private apiService: ApiService,
        private authService: AuthService,
        private router: Router,
        private cdr: ChangeDetectorRef
    ) { }

    ngOnInit() {
        if (!this.authService.isLoggedIn()) {
            this.router.navigate(['/admin/login']);
            return;
        }

        this.loadProductos();
        this.loadTalles();
        this.loadVentas();

        // Setup product search with debounce
        this.searchSubject.pipe(
            debounceTime(300),
            distinctUntilChanged(),
            switchMap(query => {
                if (query.length < 2) {
                    this.searchResults = [];
                    this.searching = false;
                    return [];
                }
                this.searching = true;
                return this.apiService.searchProducts(query);
            }),
            takeUntil(this.destroy$)
        ).subscribe({
            next: (results: any) => {
                this.searchResults = results || [];
                this.searching = false;
            },
            error: (error) => {
                console.error('Error searching products:', error);
                this.searching = false;
                this.searchResults = [];
            }
        });
    }

    ngOnDestroy() {
        this.destroy$.next();
        this.destroy$.complete();
    }

    loadProductos() {
        this.apiService.getProductos()
            .pipe(takeUntil(this.destroy$))
            .subscribe({
                next: (response: any) => {
                    this.productos = response.productos || response.items || response;
                    this.loading = false;
                },
                error: (error) => {
                    console.error('Error loading productos:', error);
                    this.error = 'Error al cargar productos';
                    this.loading = false;
                }
            });
    }

    loadTalles() {
        this.apiService.getTalles()
            .pipe(takeUntil(this.destroy$))
            .subscribe({
                next: (data: any) => {
                    this.talles = data || [];
                },
                error: (error) => {
                    console.error('Error loading talles:', error);
                }
            });
    }

    loadVentas() {
        this.loadingVentas = true;
        const params: any = {
            page: this.currentPage,
            page_size: this.pageSize
        };

        if (this.filtroProductoId) {
            params.producto_id = this.filtroProductoId;
        }
        if (this.filtroFechaDesde) {
            params.fecha_desde = this.filtroFechaDesde;
        }
        if (this.filtroFechaHasta) {
            params.fecha_hasta = this.filtroFechaHasta;
        }

        this.apiService.getVentasExternas(params)
            .pipe(takeUntil(this.destroy$))
            .subscribe({
                next: (response: any) => {
                    this.ventas = response.items || [];
                    this.totalVentas = response.total || 0;
                    this.totalPages = response.pages || 1;
                    this.loadingVentas = false;
                },
                error: (error) => {
                    console.error('Error loading ventas:', error);
                    this.error = 'Error al cargar ventas externas';
                    this.loadingVentas = false;
                }
            });
    }

    // Búsqueda de productos
    onSearchInput(event: Event) {
        const value = (event.target as HTMLInputElement).value;
        this.searchQuery = value;
        this.searchSubject.next(value);
    }


    selectProductFromSearch(producto: Producto) {
        console.log('🔵 selectProductFromSearch called with producto:', producto);
        this.productoSeleccionado = producto;
        this.nuevaVenta.producto_id = producto.id;
        this.nuevaVenta.precio_unitario = producto.precio_actual || producto.precio_base;
        this.searchQuery = producto.nombre;
        this.searchResults = [];

        console.log('🔵 About to call onProductoSeleccionado, producto_id:', this.nuevaVenta.producto_id);
        // Cargar stock
        this.onProductoSeleccionado();
    }

    clearProductSelection() {
        this.productoSeleccionado = null;
        this.nuevaVenta.producto_id = null;
        this.searchQuery = '';
        this.searchResults = [];;
        this.stockProductoSeleccionado = [];
    }

    onProductoSeleccionado() {
        console.log('🟢 onProductoSeleccionado called, producto_id:', this.nuevaVenta.producto_id);

        if (!this.nuevaVenta.producto_id) {
            console.log('🔴 No producto_id, resetting');
            this.productoSeleccionado = null;
            this.stockProductoSeleccionado = [];
            this.nuevaVenta.precio_unitario = 0;
            return;
        }

        this.productoSeleccionado = this.productos.find(p => p.id === this.nuevaVenta.producto_id) || null;
        console.log('🟢 productoSeleccionado found:', this.productoSeleccionado);

        if (this.productoSeleccionado) {
            // Pre-llenar el precio con el precio actual del producto
            this.nuevaVenta.precio_unitario = this.productoSeleccionado.precio_actual || this.productoSeleccionado.precio_base;
        }

        //  SIEMPRE cargar stock si tenemos producto_id, incluso si no encontramos el producto en la lista
        console.log('🟡 Calling apiService.getStockByProducto with ID:', this.nuevaVenta.producto_id);
        // Cargar stock disponible para este producto
        this.apiService.getStockByProducto(this.nuevaVenta.producto_id)
            .pipe(takeUntil(this.destroy$))
            .subscribe({
                next: (response: any) => {
                    console.log('🟢 Stock API response received:', response);
                    this.stockProductoSeleccionado = response.items || response || [];
                    console.log('🟢 stockProductoSeleccionado set to:', this.stockProductoSeleccionado);

                    // ✨ FORZAR actualización de la vista
                    this.cdr.detectChanges();
                },
                error: (error) => {
                    console.error('🔴 Error loading stock:', error);
                }
            });
    }

    getStockDisponible(talleId: number): number {
        const stock = this.stockProductoSeleccionado.find((s: any) => s.talle_id === talleId);
        const cantidad = stock ? stock.cantidad : 0;
        console.log(`📊 getStockDisponible(${talleId}): found stock:`, stock, 'cantidad:', cantidad);
        return cantidad;
    }

    registrarVenta() {
        this.error = '';
        this.success = '';

        // Validaciones
        if (!this.nuevaVenta.producto_id) {
            this.error = 'Debe seleccionar un producto';
            return;
        }
        if (!this.nuevaVenta.talle_id) {
            this.error = 'Debe seleccionar un talle';
            return;
        }
        if (this.nuevaVenta.cantidad <= 0) {
            this.error = 'La cantidad debe ser mayor a 0';
            return;
        }
        if (this.nuevaVenta.precio_unitario <= 0) {
            this.error = 'El precio unitario debe ser mayor a 0';
            return;
        }

        // Validar stock disponible
        const stockDisponible = this.getStockDisponible(this.nuevaVenta.talle_id);
        if (this.nuevaVenta.cantidad > stockDisponible) {
            this.error = `Stock insuficiente. Disponible: ${stockDisponible} unidades`;
            return;
        }

        this.submitting = true;

        this.apiService.crearVentaExterna(this.nuevaVenta)
            .pipe(takeUntil(this.destroy$))
            .subscribe({
                next: (response: any) => {
                    this.success = 'Venta externa registrada exitosamente. Stock descontado.';
                    this.submitting = false;

                    // Resetear formulario
                    this.resetFormulario();

                    // Recargar ventas
                    this.loadVentas();

                    // Limpiar mensaje después de 3 segundos
                    setTimeout(() => this.success = '', 3000);
                },
                error: (error) => {
                    console.error('Error registrando venta:', error);
                    this.error = error.error?.error || 'Error al registrar la venta externa';
                    this.submitting = false;
                }
            });
    }

    resetFormulario() {
        this.nuevaVenta = {
            producto_id: null,
            talle_id: null,
            cantidad: 1,
            precio_unitario: 0,
            notas: ''
        };
        this.productoSeleccionado = null;
        this.stockProductoSeleccionado = [];
        this.searchQuery = '';
        this.searchResults = [];
    }

    eliminarVenta(ventaId: number) {
        if (!confirm('¿Está seguro de eliminar esta venta? El stock será restaurado.')) {
            return;
        }

        this.apiService.eliminarVentaExterna(ventaId)
            .pipe(takeUntil(this.destroy$))
            .subscribe({
                next: () => {
                    this.success = 'Venta eliminada y stock restaurado';
                    this.loadVentas();
                    setTimeout(() => this.success = '', 3000);
                },
                error: (error) => {
                    console.error('Error eliminando venta:', error);
                    this.error = error.error?.error || 'Error al eliminar la venta';
                }
            });
    }

    aplicarFiltros() {
        this.currentPage = 1;
        this.loadVentas();
    }

    limpiarFiltros() {
        this.filtroProductoId = null;
        this.filtroFechaDesde = '';
        this.filtroFechaHasta = '';
        this.currentPage = 1;
        this.loadVentas();
    }

    // Paginación
    nextPage() {
        if (this.currentPage < this.totalPages) {
            this.currentPage++;
            this.loadVentas();
        }
    }

    previousPage() {
        if (this.currentPage > 1) {
            this.currentPage--;
            this.loadVentas();
        }
    }

    goToPage(page: number) {
        if (page >= 1 && page <= this.totalPages) {
            this.currentPage = page;
            this.loadVentas();
        }
    }

    // Helpers
    formatFecha(fechaStr: string): string {
        const fecha = new Date(fechaStr);
        return fecha.toLocaleDateString('es-AR', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit'
        });
    }

    formatPrecio(precio: number): string {
        return `$${precio.toLocaleString('es-AR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    }

    get gananciaTotal(): number {
        return this.nuevaVenta.cantidad * this.nuevaVenta.precio_unitario;
    }
}
