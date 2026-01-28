import { Component, OnInit, OnDestroy, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterModule, Router, ActivatedRoute } from '@angular/router';
import { ApiService } from '../../../services/api.service';
import { AuthService } from '../../../services/auth.service';
import { AddStockFormComponent } from './add-stock-form.component';
import { VentasExternasAdminComponent } from '../ventas-externas-admin/ventas-externas-admin';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

interface StockItem {
  id: number;
  producto_id: number;
  producto_nombre: string;
  color_id?: number;
  color_nombre?: string;
  talle_id: number;
  talle_nombre: string;
  cantidad: number;
  tiene_stock: boolean;
  updated_at: string;
  editing?: boolean;
  tempCantidad?: number;
}

@Component({
  selector: 'app-stock-admin',
  imports: [CommonModule, FormsModule, RouterModule, AddStockFormComponent, VentasExternasAdminComponent],
  templateUrl: './stock-admin.html',
  styleUrl: './stock-admin.css'
})
export class StockAdminComponent implements OnInit, OnDestroy {
  private destroy$ = new Subject<void>();

  stock: StockItem[] = [];
  productos: any[] = [];
  talles: any[] = [];
  colores: any[] = [];
  loading = true;
  loadingStock = false;  // Separate loading state for stock table

  // Paginación
  currentPage = 1;
  pageSize = 50;
  totalItems = 0;
  totalPages = 0;

  // Filtros y búsqueda
  categoriaFiltro: number | null = null;
  categorias: any[] = [];
  busqueda = '';
  ordenarPor = 'alfabetico';
  mostrarSoloStockBajo = false;
  umbralStockBajo = 5;

  // Formulario
  mostrarFormulario = false;
  mostrarFormularioAgregarStock = false;  // New: Add Stock Modal
  nuevoStock: {
    producto_id: number | null;
    color_id: number | null;
    talle_id: number | null;
    cantidad: number;
  } = {
      producto_id: null,
      color_id: null,
      talle_id: null,
      cantidad: 0
    };

  // Vista agrupada
  vistaAgrupada = false;

  // Tabs
  activeTab: 'stock' | 'ventas-externas' = 'stock';

  constructor(
    private apiService: ApiService,
    private authService: AuthService,
    private router: Router,
    private route: ActivatedRoute,
    private cdr: ChangeDetectorRef
  ) { }

  productoPreseleccionado: any = null;

  ngOnInit() {
    if (!this.authService.isLoggedIn()) {
      this.router.navigate(['/admin/login']);
      return;
    }

    // Load base data first
    this.loadProductos();
    this.loadTalles();
    this.loadColores();

    // Subscribe to route changes
    this.route.queryParams
      .pipe(takeUntil(this.destroy$))
      .subscribe((params: any) => {
        // Validación y carga de producto preseleccionado
        /*
        if (params['producto_id']) {
          const prodId = Number(params['producto_id']);
          if (!isNaN(prodId) && prodId > 0) {
            console.log('Cargando producto preseleccionado:', prodId);
            this.apiService.getProducto(prodId).subscribe({
              next: (prod) => {
                console.log('Producto cargado:', prod);
                this.productoPreseleccionado = prod;
                this.mostrarFormularioAgregarStock = true;
                this.cdr.detectChanges();
              },
              error: (err) => console.error('Error cargando producto para stock:', err)
            });
          }
        } else {
          this.productoPreseleccionado = null;
        }
        */

        this.loadStock();
      });
  }

  ngOnDestroy() {
    this.destroy$.next();
    this.destroy$.complete();
  }

  loadStock() {
    this.loadingStock = true;

    const params: any = {
      page: this.currentPage,
      page_size: this.pageSize,
      search: this.busqueda,
      solo_bajo: this.mostrarSoloStockBajo,
      umbral: this.umbralStockBajo
    };

    // Nueva lógica combinada: Ordenamiento O Filtro por Talle
    const tallesDisponibles = ['S', 'M', 'L', 'XL', 'XXL'];
    if (tallesDisponibles.includes(this.ordenarPor)) {
      params.talle_nombre = this.ordenarPor;
      params.ordenar_por = 'alfabetico'; // Por defecto A-Z si filtramos por talle
    } else {
      params.ordenar_por = this.ordenarPor;
    }

    if (this.categoriaFiltro) {
      params.categoria_id = this.categoriaFiltro;
    }

    this.apiService.getStock(params).subscribe({
      next: (response: any) => {
        // Backend now returns paginated response
        this.stock = response.items.map((item: StockItem) => ({ ...item, editing: false }));
        this.totalItems = response.total;
        this.totalPages = response.pages;
        this.currentPage = response.page;
        this.loading = false;
        this.loadingStock = false;

        // 🔥 FORZAR Change Detection
        this.cdr.detectChanges();
      },
      error: (error: any) => {
        console.error('Error cargando stock:', error);
        this.loading = false;
        this.loadingStock = false;
        this.cdr.detectChanges();
      }
    });
  }

  get stockFiltrado(): StockItem[] {
    // SIMPLIFICADO: Ya no filtramos en frontend, el backend lo hace
    return this.stock;
  }

  get stockAgrupado(): { [key: string]: StockItem[] } {
    const grupos: { [key: string]: StockItem[] } = {};
    this.stockFiltrado.forEach(item => {
      const key = item.producto_nombre;
      if (!grupos[key]) {
        grupos[key] = [];
      }
      grupos[key].push(item);
    });
    return grupos;
  }

  get productosConStockBajo(): number {
    return this.stock.filter(item => item.cantidad > 0 && item.cantidad <= this.umbralStockBajo).length;
  }

  get productosAgotados(): number {
    return this.stock.filter(item => item.cantidad === 0).length;
  }

  loadProductos() {
    // OPTIMIZADO: Usar endpoint ligero solo con id y nombre
    this.apiService.getProductosMini().subscribe({
      next: (response: any) => {
        this.productos = response.items;
      },
      error: (error: any) => {
        console.error('Error cargando productos:', error);
      }
    });

    // Cargar categorías para el filtro
    this.apiService.getCategorias(false, undefined, true).subscribe({
      next: (data: any) => {
        // Solo categorías principales (sin padre)
        this.categorias = data.filter((cat: any) => !cat.categoria_padre_id);
      },
      error: (error: any) => {
        console.error('Error cargando categorías:', error);
      }
    });
  }

  getCategoriaLabel(cat: any): string {
    return `🏠 ${cat.nombre}`;
  }

  loadTalles() {
    this.apiService.getTalles().subscribe({
      next: (data: any) => {
        this.talles = data;
      },
      error: (error: any) => {
        console.error('Error cargando talles:', error);
      }
    });
  }

  loadColores() {
    this.apiService.getColores().subscribe({
      next: (data: any) => {
        this.colores = data;
      },
      error: (error: any) => {
        console.error('Error cargando colores:', error);
      }
    });
  }

  // Edición inline
  activarEdicion(item: StockItem) {
    item.editing = true;
    item.tempCantidad = item.cantidad;
  }

  guardarEdicion(item: StockItem) {
    if (item.tempCantidad === undefined || item.tempCantidad < 0) {
      return;
    }

    this.apiService.updateStock(item.id, item.tempCantidad).subscribe({
      next: () => {
        item.cantidad = item.tempCantidad!;
        item.tiene_stock = item.cantidad > 0;
        item.editing = false;
        // Toast o notificación sutil
      },
      error: (error: any) => {
        console.error('Error actualizando stock:', error);
        alert('Error al actualizar stock');
      }
    });
  }

  cancelarEdicion(item: StockItem) {
    item.editing = false;
    item.tempCantidad = item.cantidad;
  }

  // CRUD tradicional
  nuevo() {
    this.nuevoStock = {
      producto_id: null,
      color_id: null,
      talle_id: null,
      cantidad: 0
    };
    this.mostrarFormulario = true;
  }

  guardar() {
    if (!this.nuevoStock.producto_id || !this.nuevoStock.talle_id) {
      alert('Por favor selecciona producto y talle');
      return;
    }

    this.apiService.createStock(this.nuevoStock).subscribe({
      next: () => {
        this.loadStock();
        this.cancelar();
        alert('Stock agregado exitosamente');
      },
      error: (error: any) => {
        alert('Error al guardar stock');
        console.error(error);
      }
    });
  }

  eliminar(stockId: number) {
    if (confirm('¿Estás seguro de eliminar este registro de stock?')) {
      this.apiService.deleteStock(stockId).subscribe({
        next: () => {
          this.loadStock();
        },
        error: (error: any) => {
          alert('Error al eliminar stock');
          console.error(error);
        }
      });
    }
  }

  cancelar() {
    this.mostrarFormulario = false;
    this.nuevoStock = {
      producto_id: null,
      color_id: null,
      talle_id: null,
      cantidad: 0
    };
  }

  // Filtros
  filtrarPorProducto() {
    this.loadStock();
  }

  buscar() {
    this.loadStock();
  }

  cambiarOrdenamiento() {
    this.loadStock();
  }

  limpiarBusqueda() {
    this.busqueda = '';
    this.currentPage = 1;  // Reset to first page
    this.loadStock();
  }

  limpiarFiltros() {
    this.busqueda = '';
    this.categoriaFiltro = null;
    this.ordenarPor = 'alfabetico'; // Resetear a A-Z (limpia filtro por talle)
    this.mostrarSoloStockBajo = false;
    this.currentPage = 1;  // Reset to first page
    this.loadStock();
  }

  // NUEVO: Trigger reload cuando cambia el filtro de stock bajo
  toggleStockBajo() {
    this.currentPage = 1;  // Reset to first page
    this.loadStock();
  }

  // Pagination methods
  nextPage() {
    if (this.currentPage < this.totalPages) {
      this.currentPage++;
      this.loadStock();
    }
  }

  previousPage() {
    if (this.currentPage > 1) {
      this.currentPage--;
      this.loadStock();
    }
  }

  goToPage(page: number) {
    if (page >= 1 && page <= this.totalPages) {
      this.currentPage = page;
      this.loadStock();
    }
  }

  // Open Add Stock Modal
  abrirAgregarStock() {
    this.mostrarFormularioAgregarStock = true;
  }

  cerrarAgregarStock() {
    this.mostrarFormularioAgregarStock = false;
  }

  onStockAdded() {
    // Refresh stock list after adding
    this.loadStock();
    this.cerrarAgregarStock();
  }

  // Helpers
  getStockClass(cantidad: number): string {
    if (cantidad === 0) return 'stock-agotado';
    if (cantidad <= this.umbralStockBajo) return 'stock-bajo';
    return 'stock-ok';
  }

  getStockLabel(cantidad: number): string {
    if (cantidad === 0) return 'Agotado';
    if (cantidad <= this.umbralStockBajo) return 'Stock Bajo';
    return 'Disponible';
  }
}
