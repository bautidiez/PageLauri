import { Component, OnInit, OnDestroy, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule, ActivatedRoute, Router } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../services/api.service';
import { Observable, Subject, of } from 'rxjs';
import { takeUntil, map, catchError } from 'rxjs/operators';

@Component({
  selector: 'app-productos',
  imports: [CommonModule, RouterModule, FormsModule],
  templateUrl: './productos.html',
  styleUrl: './productos.css'
})
export class ProductosComponent implements OnInit, OnDestroy {
  private destroy$ = new Subject<void>();

  productos: any[] = [];
  categorias: any[] = [];
  talles: any[] = [];
  categoriaSeleccionada: number | null = null;
  loading = true;
  loadingTimeout: any = null;

  // Paginación
  currentPage = 1;
  pageSize = 20;
  totalProducts = 0;
  hasMoreProducts = false;
  loadingMore = false;

  // Para título dinámico
  tituloActual = 'PRODUCTOS';

  // Para navegación de sidebar
  currentCategoryLevel: number = 0; // 0 = ninguna, 1 = principal, 2 = subcategoría
  parentCategory: any = null;
  currentCategory: any = null;

  // Búsqueda
  busqueda = '';

  // Filtros
  filtros = {
    categoria_id: null as number | null,
    destacados: false,
    color: '',
    talle_id: null as number | null,
    dorsal: '',
    numero: null as number | null,
    version: '',
    precio_min: null as number | null,
    precio_max: null as number | null,
    ordenar_por: 'destacado' as string
  };

  // Opciones de filtros disponibles
  coloresDisponibles: string[] = [];
  dorsalesDisponibles: string[] = [];
  numerosDisponibles: number[] = [];
  versionesDisponibles: string[] = ['Hincha', 'Jugador'];

  // UI
  mostrarFiltros = false;
  precioMinInput = '';
  precioMaxInput = '';

  // Category slug mapping
  private categorySlugMap: { [key: string]: number } = {};
  private categoryIdToSlug: { [key: number]: string } = {};

  constructor(
    private apiService: ApiService,
    private route: ActivatedRoute,
    private router: Router,
    private cdr: ChangeDetectorRef
  ) { }

  ngOnInit() {
    console.log('🚀 [ProductosComponent] ngOnInit EJECUTADO');

    // Load categories and talles first
    this.loadCategorias().subscribe(() => {
      console.log('✅ [ProductosComponent] loadCategorias COMPLETADO');

      // ✅ FIX: Call handleRouteParams IMMEDIATELY on initial load
      this.handleRouteParams();

      // Then subscribe to route changes ONCE with proper cleanup
      this.route.params
        .pipe(takeUntil(this.destroy$))
        .subscribe(() => {
          console.log('🔄 [ProductosComponent] route.params CAMBIÓ');
          this.handleRouteParams();
        });
    });

    this.loadTalles();
  }

  ngOnDestroy() {
    this.destroy$.next();
    this.destroy$.complete();
  }

  private handleRouteParams() {
    console.log('📍 [ProductosComponent] handleRouteParams EJECUTADO');
    const params = this.route.snapshot.params;
    const queryParams = this.route.snapshot.queryParams;

    // Handle query params (búsqueda y ofertas)
    if (queryParams['busqueda']) {
      this.busqueda = queryParams['busqueda'];
    }
    if (queryParams['ofertas'] === 'true') {
      this.filtros.destacados = false;
    }

    // Determine category from params
    // Routes: 'categoria/:slug', 'categoria/:parent/:slug', 'categoria/:grandparent/:parent/:slug'
    // The last param is always the leaf category we want to filter by.

    const slug = params['slug'];
    // const parentSlug = params['parent'];
    // const grandparentSlug = params['grandparent'];

    // Simplification: We only really need the 'slug' (the last one) to find the ID.
    // However, if we want to validatte path, we could check parents.
    // For now, trusting the unique slug or finding first match is enough for filtering.
    // But if duplicate slugs exist (e.g. 'hombre' under 'Remeras' and 'Shorts'), we need context.

    // Implementation: Try to match the leaf slug.
    // TODO: Ideally use parent slugs to disambiguate if needed. 
    // For now, getCategoryIdFromSlug returns the first match.

    if (slug) {
      const categoryId = this.getCategoryIdFromSlug(slug);
      if (categoryId) {
        this.filtros.categoria_id = categoryId;
      } else {
        console.warn('Slug not found:', slug);
        // Optionally try to find by ID if slug is numeric (fallback)
        if (!isNaN(+slug)) {
          this.filtros.categoria_id = +slug;
        }
      }
    }
    // Fallback for old simple ID routes
    else if (params['id']) {
      this.filtros.categoria_id = +params['id'];
    }
    else {
      this.filtros.categoria_id = null;
    }

    console.log('📍 Filtro categoría ID:', this.filtros.categoria_id);

    this.loadProductos();
    this.actualizarTitulo(); // Will be called again after loadCategorias if not ready
    this.updateCategoryContext();
  }

  private getCategoryIdFromSlug(slug: string): number | null {
    const normalizedSlug = this.normalizeSlug(slug);
    return this.categorySlugMap[normalizedSlug] || null;
  }

  private getSubcategoryId(parentId: number, subcategorySlug: string): number | null {
    const normalizedSlug = this.normalizeSlug(subcategorySlug);
    const parentCategory = this.categorias.find(c => c.id === parentId);
    if (parentCategory && parentCategory.subcategorias) {
      const subcategory = parentCategory.subcategorias.find((sub: any) =>
        this.normalizeSlug(sub.nombre) === normalizedSlug
      );
      return subcategory ? subcategory.id : null;
    }
    return null;
  }

  private normalizeSlug(text: string): string {
    return text.toLowerCase()
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '') // Remove accents
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/^-+|-+$/g, '');
  }

  actualizarTitulo() {
    const ofertas = this.route.snapshot.queryParams['ofertas'];
    if (ofertas === 'true') {
      this.tituloActual = 'OFERTAS';
      return;
    }

    const categoriaId = this.filtros.categoria_id;
    if (!categoriaId) {
      this.tituloActual = 'PRODUCTOS';
      return;
    }

    // Buscar la categoría seleccionada recursivamente
    const categoria = this.findCategoryById(categoriaId);

    if (categoria) {
      // Build breadcrumb parts
      const parts = [categoria.nombre.toUpperCase()];
      let parentId = categoria.categoria_padre_id;

      while (parentId) {
        const parent = this.findCategoryById(parentId);
        if (parent) {
          parts.unshift(parent.nombre.toUpperCase());
          parentId = parent.categoria_padre_id;
        } else {
          break; // Safety break
        }
      }

      this.tituloActual = parts.join(' > ');
      return;
    }

    // Si no se encuentra, usar PRODUCTOS por defecto
    const slugParams = this.route.snapshot.params['slug'];
    const mapSize = Object.keys(this.categorySlugMap).length;
    this.tituloActual = `PRODUCTOS (ID:${categoriaId} Slug:${slugParams} Map:${mapSize})`;
  }

  loadProductos() {
    console.log('🔄 [ProductosComponent] loadProductos EJECUTADO');
    this.loading = true;
    this.currentPage = 1; // Reset a página 1

    const filtrosEnviar: any = {};
    if (this.busqueda) filtrosEnviar.busqueda = this.busqueda;
    if (this.filtros.categoria_id) filtrosEnviar.categoria_id = this.filtros.categoria_id;
    if (this.filtros.destacados) filtrosEnviar.destacados = true;
    if (this.filtros.color) filtrosEnviar.color = this.filtros.color;
    if (this.filtros.talle_id) filtrosEnviar.talle_id = this.filtros.talle_id;
    if (this.filtros.dorsal) filtrosEnviar.dorsal = this.filtros.dorsal;
    if (this.filtros.numero !== null) filtrosEnviar.numero = this.filtros.numero;
    if (this.filtros.version) filtrosEnviar.version = this.filtros.version;
    if (this.filtros.precio_min !== null) filtrosEnviar.precio_min = this.filtros.precio_min;
    if (this.filtros.precio_max !== null) filtrosEnviar.precio_max = this.filtros.precio_max;
    if (this.filtros.ordenar_por) filtrosEnviar.ordenar_por = this.filtros.ordenar_por;

    // Use snapshot instead of subscribe for one-time read
    const queryParams = this.route.snapshot.queryParams;
    if (queryParams['ofertas'] === 'true') {
      filtrosEnviar.ofertas = true;
    }

    // Paginación (cargar 20 por página)
    filtrosEnviar.page = 1;
    filtrosEnviar.page_size = this.pageSize;

    console.log('🔄 Filtros enviados:', filtrosEnviar);

    this.apiService.getProductos(filtrosEnviar).subscribe({
      next: (data) => {
        console.log('📦 [ProductosComponent] DATOS RECIBIDOS del API:', data);

        // Manejar respuesta paginada o array directo
        this.productos = data.items || data;
        this.totalProducts = data.total || this.productos.length;
        this.hasMoreProducts = this.productos.length < this.totalProducts;

        console.log('📋 [ProductosComponent] PRODUCTOS ASIGNADOS:', this.productos.length, 'productos');
        console.log('📋 Array productos:', this.productos);

        this.extraerOpcionesFiltros();
        this.loading = false;

        console.log('✅ [ProductosComponent] Loading = false, vista debería actualizarse');

        // 🔥 FORZAR Change Detection
        this.cdr.detectChanges();
        console.log('🔥 [ProductosComponent] detectChanges() EJECUTADO - Vista actualizada');
      },
      error: (error) => {
        console.error('❌ [ProductosComponent] ERROR cargando productos:', error);
        this.loading = false;
        this.cdr.detectChanges();
      }
    });
  }

  loadMoreProductos() {
    if (this.loadingMore || !this.hasMoreProducts) return;

    this.loadingMore = true;
    this.currentPage++;

    const filtrosEnviar: any = {};
    if (this.busqueda) filtrosEnviar.busqueda = this.busqueda;
    if (this.filtros.categoria_id) filtrosEnviar.categoria_id = this.filtros.categoria_id;
    if (this.filtros.destacados) filtrosEnviar.destacados = true;
    if (this.filtros.color) filtrosEnviar.color = this.filtros.color;
    if (this.filtros.talle_id) filtrosEnviar.talle_id = this.filtros.talle_id;
    if (this.filtros.dorsal) filtrosEnviar.dorsal = this.filtros.dorsal;
    if (this.filtros.numero !== null) filtrosEnviar.numero = this.filtros.numero;
    if (this.filtros.version) filtrosEnviar.version = this.filtros.version;
    if (this.filtros.precio_min !== null) filtrosEnviar.precio_min = this.filtros.precio_min;
    if (this.filtros.precio_max !== null) filtrosEnviar.precio_max = this.filtros.precio_max;
    if (this.filtros.ordenar_por) filtrosEnviar.ordenar_por = this.filtros.ordenar_por;

    // Use snapshot instead of subscribe
    const queryParams = this.route.snapshot.queryParams;
    if (queryParams['ofertas'] === 'true') {
      filtrosEnviar.ofertas = true;
    }

    // Paginación
    filtrosEnviar.page = this.currentPage;
    filtrosEnviar.page_size = this.pageSize;

    this.apiService.getProductos(filtrosEnviar).subscribe({
      next: (data) => {
        const newProducts = data.items || data;
        this.productos = [...this.productos, ...newProducts]; // APPEND
        this.totalProducts = data.total || this.productos.length;
        this.hasMoreProducts = this.productos.length < this.totalProducts;
        this.extraerOpcionesFiltros();
        this.loadingMore = false;
      },
      error: (error) => {
        console.error('Error cargando más productos:', error);
        this.loadingMore = false;
      }
    });
  }

  extraerOpcionesFiltros() {
    const colores = new Set<string>();
    const dorsales = new Set<string>();
    const numeros = new Set<number>();
    const versiones = new Set<string>();

    this.productos.forEach(p => {
      if (p.color) colores.add(p.color);
      if (p.dorsal) dorsales.add(p.dorsal);
      if (p.numero !== null) numeros.add(p.numero);
      if (p.version) versiones.add(p.version);
    });

    this.coloresDisponibles = Array.from(colores).sort();
    this.dorsalesDisponibles = Array.from(dorsales).sort();
    this.numerosDisponibles = Array.from(numeros).sort((a, b) => a - b);
    // this.versionesDisponibles = Array.from(versiones).sort();
    // Mantenemos las estáticas 'Hincha' y 'Jugador' siempre visibles
    // O si queremos agregar dinámicas que no estén en la lista estática:
    const versionesDinamicas = Array.from(versiones);
    versionesDinamicas.forEach(v => {
      if (!this.versionesDisponibles.includes(v)) {
        this.versionesDisponibles.push(v);
      }
    });
    this.versionesDisponibles.sort();
  }

  loadCategorias(): Observable<void> {
    // Request a flat list (flat=true) to build our own tree reliably
    return this.apiService.getCategorias(true, undefined, true).pipe(
      map((data: any[]) => {
        console.log('📦 [ProductosComponent] Categorías flat recibidas:', data.length);

        // Build a Map for O(1) access
        const categoryMap = new Map();
        data.forEach((cat: any) => {
          // Initialize/Reset subcategorias for our local tree building
          cat.subcategorias = [];
          categoryMap.set(cat.id, cat);
        });

        // Assemble the tree from the flat mapping
        const roots: any[] = [];
        data.forEach((cat: any) => {
          if (cat.categoria_padre_id) {
            const parent = categoryMap.get(cat.categoria_padre_id);
            if (parent) {
              parent.subcategorias.push(cat);
            } else {
              // If parent not found/active, treat as root or ignore? 
              // Usually orphaned subcats should be ignored or root.
              console.warn(`Orphaned category: ${cat.nombre} (Parent ID: ${cat.categoria_padre_id})`);
            }
          } else {
            roots.push(cat);
          }
        });

        // Sort subcategories by name alphabetically
        data.forEach(cat => {
          if (cat.subcategorias) {
            cat.subcategorias.sort((a: any, b: any) => a.nombre.localeCompare(b.nombre));
          }
        });

        this.categorias = roots.sort((a, b) => a.nombre.localeCompare(b.nombre));

        // Build slug mapping (recursive)
        this.buildSlugMap();

        // Actualizar el título y contexto
        this.actualizarTitulo();
        if (this.route.snapshot.params['id'] || this.route.snapshot.params['slug']) {
          this.updateCategoryContext();
        }

        // 🔥 FORZAR Change Detection
        this.cdr.detectChanges();
      }),
      catchError((error) => {
        console.error('Error cargando categorías:', error);
        return of(void 0);
      })
    );
  }

  private buildSlugMap() {
    const mapRecursive = (list: any[]) => {
      list.forEach(cat => {
        // Use the slug from the DB if available, otherwise normalize the name
        // This is CRITICAL because the router links use cat.slug
        const slug = cat.slug ? cat.slug : this.normalizeSlug(cat.nombre);

        this.categorySlugMap[slug] = cat.id;
        this.categoryIdToSlug[cat.id] = slug;

        if (cat.subcategorias && cat.subcategorias.length > 0) {
          mapRecursive(cat.subcategorias);
        }
      });
    };

    mapRecursive(this.categorias);
  }

  loadTalles() {
    this.apiService.getTalles().subscribe({
      next: (data) => {
        this.talles = data;
      },
      error: (error) => {
        console.error('Error cargando talles:', error);
      }
    });
  }

  filtrarPorCategoria(categoriaId: number | null) {
    this.filtros.categoria_id = categoriaId;

    // Actualizar la URL para reflejar la categoría seleccionada
    if (categoriaId) {
      this.router.navigate(['/categoria', categoriaId]);
    } else {
      this.router.navigate(['/productos']);
    }

    this.loadProductos();
    this.actualizarTitulo();
  }

  toggleDestacados() {
    this.filtros.destacados = !this.filtros.destacados;
    this.loadProductos();
  }

  aplicarFiltros() {
    // Convertir precio inputs a números
    this.filtros.precio_min = this.precioMinInput ? parseFloat(this.precioMinInput) : null;
    this.filtros.precio_max = this.precioMaxInput ? parseFloat(this.precioMaxInput) : null;
    this.loadProductos();
  }

  limpiarFiltros() {
    this.filtros = {
      categoria_id: null,
      destacados: false,
      color: '',
      talle_id: null,
      dorsal: '',
      numero: null,
      version: '',
      precio_min: null,
      precio_max: null,
      ordenar_por: 'destacado'
    };
    this.precioMinInput = '';
    this.precioMaxInput = '';
    this.busqueda = '';
    this.loadProductos();
  }

  cambiarOrdenamiento(orden: string) {
    this.filtros.ordenar_por = orden;
    this.loadProductos();
  }

  buscar() {
    this.loadProductos();
  }

  getImagenPrincipal(producto: any): string {
    const apiBase = this.apiService.getApiUrl().replace('/api', '');
    if (producto.imagenes && producto.imagenes.length > 0) {
      const principal = producto.imagenes.find((img: any) => img.es_principal);
      if (principal) {
        return `${apiBase}${principal.url}`;
      }
      return `${apiBase}${producto.imagenes[0].url}`;
    }
    return 'https://via.placeholder.com/300x300?text=Sin+imagen';
  }

  getPrecioTransferencia(producto: any): number {
    // 15% de descuento con transferencia sobre el mejor precio
    return this.getPrecioFinal(producto) * 0.85;
  }

  // Obtener el mejor precio disponible (base, descuento directo o promoción)
  getPrecioFinal(producto: any): number {
    let mejorPrecio = producto.precio_descuento || producto.precio_base;

    if (producto.promociones && producto.promociones.length > 0) {
      const promo = producto.promociones[0];
      const tipo = (promo.tipo_promocion_nombre || '').toLowerCase();
      const valor = promo.valor || 0;

      if (tipo.includes('porcentaje')) {
        const precioPromo = producto.precio_base * (1 - (valor / 100));
        if (precioPromo < mejorPrecio) mejorPrecio = precioPromo;
      } else if (tipo.includes('fijo')) {
        const precioPromo = Math.max(0, producto.precio_base - valor);
        if (precioPromo < mejorPrecio) mejorPrecio = precioPromo;
      }
    }

    return mejorPrecio;
  }

  getDescuentoPorcentaje(producto: any): number {
    const precioBase = producto.precio_base;
    const precioFinal = this.getPrecioFinal(producto);

    if (!precioBase || precioFinal >= precioBase) return 0;
    return Math.round((1 - (precioFinal / precioBase)) * 100);
  }

  // Obtener texto para el badge de promoción
  getBadgeText(producto: any): string {
    if (!producto.promociones || producto.promociones.length === 0) return '';
    const promo = producto.promociones[0];
    const tipo = (promo.tipo_promocion_nombre || '').toLowerCase();

    if (tipo.includes('porcentaje')) return `${promo.valor}% OFF`;
    if (tipo.includes('fijo')) return `$${promo.valor} OFF`;
    if (tipo.includes('2x1')) return '2x1';
    if (tipo.includes('3x2')) return '3x2';

    return promo.tipo_promocion_nombre;
  }

  getCuotaSinInteres(producto: any): number {
    // Dividir precio final en 3 cuotas sin interés
    return this.getPrecioFinal(producto) / 3;
  }

  getOrdenamientoTexto(): string {
    const ordenamientos: any = {
      'destacado': 'Destacado',
      'mas_vendido': 'Más Vendido',
      'alfabetico': 'Orden Alfabético',
      'precio_asc': 'Precio: Menor a Mayor',
      'precio_desc': 'Precio: Mayor a Menor'
    };
    return ordenamientos[this.filtros.ordenar_por] || 'Destacado';
  }

  updateCategoryContext() {
    const categoriaId = this.filtros.categoria_id;

    if (!categoriaId) {
      this.currentCategoryLevel = 0;
      this.currentCategory = null;
      this.parentCategory = null;
      return;
    }

    const cat = this.findCategoryById(categoriaId);

    if (cat) {
      this.currentCategory = cat;
      // Calculate level based on parents
      let level = 1;
      let parentId = cat.categoria_padre_id;
      let parent = null;

      while (parentId) {
        level++;
        const p = this.findCategoryById(parentId);
        if (p) {
          if (level === 2) this.parentCategory = p; // Immediate parent
          parentId = p.categoria_padre_id;
        } else {
          break;
        }
      }
      this.currentCategoryLevel = level;

      // If immediate parent is needed for "Back" button, find it direct
      if (cat.categoria_padre_id) {
        this.parentCategory = this.findCategoryById(cat.categoria_padre_id);
      } else {
        this.parentCategory = null;
      }
    }
  }

  getSidebarCategories(): any[] {
    // Nivel 0 (Home productos): Mostrar raíces
    if (this.currentCategoryLevel === 0) {
      return this.categorias;
    }

    // Si estamos en una categoría...
    if (this.currentCategory) {
      // ¿Tiene subcategorías? Mostrarlas (Drill down)
      if (this.currentCategory.subcategorias && this.currentCategory.subcategorias.length > 0) {
        return this.currentCategory.subcategorias;
      }

      // Si NO tiene subcategorías, es una hoja. 
      // Mostrar los hermanos (subcategorías del padre) para no dejar el sidebar vacío
      if (this.parentCategory && this.parentCategory.subcategorias) {
        return this.parentCategory.subcategorias;
      }

      // Si es una categoría raíz sin hijos (caso raro pero posible)
      if (this.currentCategoryLevel === 1) {
        return this.categorias;
      }

      return [];
    }

    return this.categorias;
  }

  getSidebarTitle(): string {
    if (this.currentCategoryLevel === 0) {
      return 'CATEGORÍAS';
    }
    if (this.currentCategory) {
      // Si estamos mostrando los hijos de la actual, el titulo es la actual.
      if (this.currentCategory.subcategorias && this.currentCategory.subcategorias.length > 0) {
        return this.currentCategory.nombre.toUpperCase();
      }
      // Si estamos mostrando hermanos, el título es el del padre.
      if (this.parentCategory) {
        return this.parentCategory.nombre.toUpperCase();
      }

      return this.currentCategory.nombre.toUpperCase();
    }
    return 'CATEGORÍAS';
  }

  getCategoryPath(category: any): any[] {
    const slug = this.categoryIdToSlug[category.id];
    if (!slug) return ['/productos'];

    const pathParts = [slug];
    let parentId = category.categoria_padre_id;

    // Walk up the tree to prepend parent slugs
    while (parentId) {
      const parent = this.findCategoryById(parentId);
      if (parent) {
        const parentSlug = this.categoryIdToSlug[parent.id];
        if (parentSlug) {
          pathParts.unshift(parentSlug);
        }
        parentId = parent.categoria_padre_id;
      } else {
        break;
      }
    }

    return ['/categoria', ...pathParts];
  }

  findCategoryById(id: number): any {
    const findInArray = (list: any[]): any => {
      for (const cat of list) {
        if (cat.id === id) return cat;
        if (cat.subcategorias && cat.subcategorias.length > 0) {
          const found = findInArray(cat.subcategorias);
          if (found) return found;
        }
      }
      return null;
    };
    return findInArray(this.categorias);
  }

  navigateToCategory(categoriaId: number) {
    const category = this.findCategoryById(categoriaId);
    if (category) {
      const path = this.getCategoryPath(category);
      this.router.navigate(path).then(() => {
        this.updateCategoryContext();
      });
    } else {
      // Fallback
      this.router.navigate(['/categoria', categoriaId]);
    }
  }

  navigateBack() {
    if (this.parentCategory) {
      this.navigateToCategory(this.parentCategory.id);
    } else {
      // If no parent, go to root (Productos)
      this.router.navigate(['/productos']);
    }
  }
}
