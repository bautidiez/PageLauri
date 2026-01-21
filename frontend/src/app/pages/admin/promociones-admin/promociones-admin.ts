import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterModule, Router } from '@angular/router';
import { ApiService } from '../../../services/api.service';
import { AuthService } from '../../../services/auth.service';

interface Promocion {
  id: number;
  alcance: 'producto' | 'categoria' | 'tienda';
  productos_ids: number[];
  productos_nombres?: string[];
  categorias_ids: number[];
  categorias_nombres?: string[];
  tipo_promocion_id: number;
  tipo_nombre?: string;
  valor: number;
  activa: boolean;
  fecha_inicio: string;
  fecha_fin: string;
  estado?: 'activa' | 'programada' | 'expirada';
  es_cupon?: boolean;
  codigo?: string;
  envio_gratis?: boolean;
}

@Component({
  selector: 'app-promociones-admin',
  imports: [CommonModule, FormsModule, RouterModule],
  templateUrl: './promociones-admin.html',
  styleUrl: './promociones-admin.css'
})
export class PromocionesAdminComponent implements OnInit {
  promociones: Promocion[] = [];
  tiposPromocion: any[] = [];
  productos: any[] = [];
  categorias: any[] = [];
  loading = true;

  // Autocomplete
  searchQuery = '';
  searchResults: any[] = [];
  searching = false;
  productosSeleccionados: any[] = [];
  categoriasSeleccionadas: number[] = [];

  // Wizard
  mostrarWizard = false;
  pasoActual = 1;
  totalPasos = 2;

  nuevaPromocion: any = {
    alcance: 'producto',
    productos_ids: [],
    categorias_ids: [],
    tipo_promocion_id: null,
    valor: null,
    activa: true,
    fecha_inicio: '',
    fecha_fin: '',
    es_cupon: false,
    codigo: '',
    envio_gratis: false
  };

  modoEdicion = false;
  promocionEditando: any = null;

  // Filtros
  filtroEstado: 'todas' | 'activas' | 'programadas' | 'expiradas' = 'todas';
  busqueda = '';

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
    this.loadPromociones();
    this.loadTiposPromocion();
    this.loadProductos();
    this.loadCategorias();
  }

  loadPromociones() {
    if (this.promociones.length === 0) {
      this.loading = true;
    }

    this.apiService.get('/admin/promociones').subscribe({
      next: (data: Promocion[]) => {
        this.promociones = data.map(p => ({
          ...p,
          estado: this.getEstadoPromocion(p.fecha_inicio, p.fecha_fin, p.activa)
        }));
        this.loading = false;
        this.cdr.detectChanges();
      },
      error: (error: any) => {
        console.error('Error cargando promociones:', error);
        this.loading = false;
        this.cdr.detectChanges();
      }
    });
  }

  get promocionesFiltradas(): Promocion[] {
    let filtradas = this.promociones;

    // Filtro por estado
    if (this.filtroEstado !== 'todas') {
      filtradas = filtradas.filter(p => p.estado === this.filtroEstado as any);
    }

    // Búsqueda
    if (this.busqueda.trim()) {
      const termino = this.busqueda.toLowerCase();
      filtradas = filtradas.filter(p =>
        (p.productos_nombres || []).some(n => n.toLowerCase().includes(termino)) ||
        (p.categorias_nombres || []).some(n => n.toLowerCase().includes(termino)) ||
        (p.tipo_nombre || '').toLowerCase().includes(termino)
      );
    }

    return filtradas;
  }

  get stats() {
    return {
      activas: this.promociones.filter(p => p.estado === 'activa').length,
      programadas: this.promociones.filter(p => p.estado === 'programada').length,
      expiradas: this.promociones.filter(p => p.estado === 'expirada').length
    };
  }

  loadTiposPromocion() {
    this.apiService.getTiposPromocion().subscribe({
      next: (data: any) => {
        this.tiposPromocion = data;
      },
      error: (error: any) => {
        console.error('Error cargando tipos de promoción:', error);
      }
    });
  }

  loadProductos() {
    this.apiService.getProductos().subscribe({
      next: (data: any) => {
        this.productos = data.items || data;
      },
      error: (error: any) => {
        console.error('Error cargando productos:', error);
      }
    });
  }

  loadCategorias() {
    this.apiService.getCategorias(true).subscribe({
      next: (data: any) => {
        this.categorias = data;
      },
      error: (error: any) => {
        console.error('Error cargando categorías:', error);
      }
    });
  }

  nuevo() {
    this.modoEdicion = false;
    this.promocionEditando = null;
    const hoy = new Date();
    const fin = new Date();
    fin.setMonth(fin.getMonth() + 1);

    this.nuevaPromocion = {
      alcance: 'producto',
      productos_ids: [],
      categorias_ids: [],
      tipo_promocion_id: null,
      valor: null,
      activa: true,
      fecha_inicio: hoy.toISOString().split('T')[0],
      fecha_fin: fin.toISOString().split('T')[0],
      es_cupon: false,
      codigo: '',
      envio_gratis: false
    };
    this.productosSeleccionados = [];
    this.categoriasSeleccionadas = [];
    this.searchQuery = '';
    this.pasoActual = 1;
    this.mostrarWizard = true;
  }

  editar(promocion: Promocion) {
    this.modoEdicion = true;
    this.promocionEditando = promocion;
    this.nuevaPromocion = {
      alcance: promocion.alcance || 'producto',
      productos_ids: promocion.productos_ids || [],
      categorias_ids: promocion.categorias_ids || [],
      tipo_promocion_id: promocion.tipo_promocion_id,
      valor: promocion.valor,
      activa: promocion.activa,
      fecha_inicio: promocion.fecha_inicio.split('T')[0],
      fecha_fin: promocion.fecha_fin.split('T')[0],
      es_cupon: promocion.es_cupon || false,
      codigo: promocion.codigo || '',
      envio_gratis: promocion.envio_gratis || false
    };

    // Cargar visualmente productos seleccionados
    if (this.nuevaPromocion.productos_ids.length > 0) {
      this.productosSeleccionados = this.productos.filter(p => this.nuevaPromocion.productos_ids.includes(p.id));
    } else {
      this.productosSeleccionados = [];
    }
    this.categoriasSeleccionadas = [...this.nuevaPromocion.categorias_ids];
    this.pasoActual = 1;
    this.mostrarWizard = true;
  }

  siguientePaso() {
    if (this.pasoActual === 1) {
      if (this.nuevaPromocion.alcance === 'producto' && this.productosSeleccionados.length === 0) {
        alert('Por favor selecciona al menos un producto');
        return;
      }
      if (this.nuevaPromocion.alcance === 'categoria' && this.categoriasSeleccionadas.length === 0) {
        alert('Por favor selecciona al menos una categoría');
        return;
      }
      if (!this.nuevaPromocion.tipo_promocion_id) {
        alert('Por favor selecciona el tipo de promoción');
        return;
      }
      if (this.mostrarCampoValor() && !this.nuevaPromocion.valor) {
        alert('Por favor ingresa el valor de la promoción');
        return;
      }
      if (this.nuevaPromocion.es_cupon && !this.nuevaPromocion.codigo) {
        alert('Por favor ingresa el código del cupón');
        return;
      }
    }
    if (this.pasoActual < this.totalPasos) {
      this.pasoActual++;
    }
  }

  pasoAnterior() {
    if (this.pasoActual > 1) {
      this.pasoActual--;
    }
  }

  guardar() {
    if (!this.validarFechas()) {
      alert('La fecha de fin debe ser posterior a la fecha de inicio');
      return;
    }

    // Asegurar IDs antes de enviar
    this.nuevaPromocion.productos_ids = this.productosSeleccionados.map(p => p.id);
    this.nuevaPromocion.categorias_ids = this.categoriasSeleccionadas;

    const promocionData = {
      ...this.nuevaPromocion,
      valor: this.nuevaPromocion.valor || 0,
      fecha_inicio: new Date(this.nuevaPromocion.fecha_inicio + 'T00:00:00').toISOString(),
      fecha_fin: new Date(this.nuevaPromocion.fecha_fin + 'T23:59:59').toISOString()
    };

    const request = this.modoEdicion
      ? this.apiService.updatePromocion(this.promocionEditando!.id, promocionData)
      : this.apiService.createPromocion(promocionData);

    request.subscribe({
      next: () => {
        alert(this.modoEdicion ? 'Promoción actualizada' : 'Promoción creada exitosamente');
        this.loadPromociones();
        this.cancelar();
      },
      error: (error: any) => {
        alert('Error al guardar promoción');
        console.error(error);
      }
    });
  }

  eliminar(promocionId: number) {
    if (confirm('¿Estás seguro de eliminar esta promoción?')) {
      this.apiService.deletePromocion(promocionId).subscribe({
        next: () => {
          this.loadPromociones();
          alert('Promoción eliminada');
        },
        error: (error: any) => {
          alert('Error al eliminar promoción');
          console.error(error);
        }
      });
    }
  }

  cancelar() {
    this.mostrarWizard = false;
    this.modoEdicion = false;
    this.promocionEditando = null;
    this.pasoActual = 1;
  }

  // Helpers
  getEstadoPromocion(inicio: string, fin: string, activa: boolean): 'activa' | 'programada' | 'expirada' {
    if (!activa) return 'expirada';

    const ahora = new Date();
    const fechaInicio = new Date(inicio);
    const fechaFin = new Date(fin);

    if (ahora < fechaInicio) return 'programada';
    if (ahora > fechaFin) return 'expirada';
    return 'activa';
  }

  getEstadoClass(estado: string): string {
    return `badge-${estado}`;
  }

  getEstadoLabel(estado: string): string {
    const labels: any = {
      'activa': 'Activa',
      'programada': 'Programada',
      'expirada': 'Expirada'
    };
    return labels[estado] || estado;
  }

  getTipoPromocionNombre(tipoId: number): string {
    const tipo = this.tiposPromocion.find(t => t.id === tipoId);
    return tipo ? tipo.descripcion : 'N/A';
  }

  getTipoSeleccionado(): any {
    if (!this.nuevaPromocion.tipo_promocion_id) return null;
    return this.tiposPromocion.find(t => t.id === this.nuevaPromocion.tipo_promocion_id);
  }

  mostrarCampoValor(): boolean {
    const tipo = this.getTipoSeleccionado();
    if (!tipo) return false;
    // Si es envío gratis, no se necesita valor (se aplica automáticamente al alcance seleccionado)
    if (this.nuevaPromocion.envio_gratis) return false;
    return tipo.nombre === 'descuento_porcentaje' || tipo.nombre === 'descuento_fijo';
  }

  getPlaceholderValor(): string {
    const tipo = this.getTipoSeleccionado();
    if (!tipo) return '';
    if (tipo.nombre === 'descuento_porcentaje') return 'Ej: 20 para 20%';
    if (tipo.nombre === 'descuento_fijo') return 'Ej: 2000 para $2000';
    return '';
  }

  validarFechas(): boolean {
    const inicio = new Date(this.nuevaPromocion.fecha_inicio);
    const fin = new Date(this.nuevaPromocion.fecha_fin);
    return fin > inicio;
  }

  formatFecha(fecha: string): string {
    if (!fecha) return '-';
    // Si la fecha viene como "YYYY-MM-DD", la procesamos como local
    if (fecha.includes('-') && !fecha.includes('T')) {
      const [year, month, day] = fecha.split('-').map(Number);
      return new Date(year, month - 1, day).toLocaleDateString('es-AR');
    }
    return new Date(fecha).toLocaleDateString('es-AR');
  }

  getProductoNombre(productoId: number | null): string {
    if (!productoId) return '-';
    const producto = this.productos.find(p => p.id === productoId);
    return producto ? producto.nombre : '-';
  }

  getDiasRestantes(fechaFin: string): number {
    const ahora = new Date();
    const fin = new Date(fechaFin);
    const diff = fin.getTime() - ahora.getTime();
    return Math.ceil(diff / (1000 * 60 * 60 * 24));
  }

  // Autocomplete Products
  onSearchInput() {
    if (this.searchQuery.length < 2) {
      this.searchResults = [];
      return;
    }

    this.searching = true;
    this.apiService.searchProducts(this.searchQuery).subscribe({
      next: (results) => {
        // Filtrar productos que ya están seleccionados
        this.searchResults = results.filter((p: any) =>
          !this.productosSeleccionados.some(sel => sel.id === p.id)
        );
        this.searching = false;
        this.cdr.detectChanges();
      },
      error: () => {
        this.searching = false;
        this.searchResults = [];
        this.cdr.detectChanges();
      }
    });
  }

  selectProduct(product: any) {
    if (!this.productosSeleccionados.some(p => p.id === product.id)) {
      this.productosSeleccionados.push(product);
    }
    this.searchQuery = '';
    this.searchResults = [];
  }

  removeProduct(productId: number) {
    this.productosSeleccionados = this.productosSeleccionados.filter(p => p.id !== productId);
  }

  // Categories
  toggleCategoria(catId: number) {
    const index = this.categoriasSeleccionadas.indexOf(catId);
    if (index > -1) {
      this.categoriasSeleccionadas.splice(index, 1);
    } else {
      this.categoriasSeleccionadas.push(catId);
    }
  }

  isCategoriaSelected(catId: number): boolean {
    return this.categoriasSeleccionadas.includes(catId);
  }

  getCategoryLabel(catId: number): string {
    const cat = this.categorias.find(c => c.id === catId);
    if (!cat) return '-';

    if (!cat.categoria_padre_id) {
      return cat.nombre;
    }

    const padre = this.categorias.find(p => p.id === cat.categoria_padre_id);
    return padre ? `${this.getCategoryLabel(padre.id)} > ${cat.nombre}` : cat.nombre;
  }

  getAlcanceResumen(): string {
    const a = this.nuevaPromocion.alcance;
    if (a === 'tienda') return 'Toda la tienda';
    if (a === 'producto') return `${this.productosSeleccionados.length} producto(s)`;
    if (a === 'categoria') return `${this.categoriasSeleccionadas.length} categoría(s)`;
    return '-';
  }
}
