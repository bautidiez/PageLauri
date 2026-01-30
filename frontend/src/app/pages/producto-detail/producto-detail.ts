import { Component, OnInit, OnDestroy, ChangeDetectorRef, NgZone } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router, RouterModule } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../services/api.service';
import { CartService } from '../../services/cart.service';
import { SeoService } from '../../services/seo.service';
import { ShippingCalculatorComponent } from '../../components/shipping-calculator/shipping-calculator';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

@Component({
  selector: 'app-producto-detail',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule, ShippingCalculatorComponent],
  templateUrl: './producto-detail.html',
  styleUrl: './producto-detail.css'
})
export class ProductoDetailComponent implements OnInit, OnDestroy {
  producto: any = null;
  talles: any[] = [];
  talleSeleccionado: any = null;
  cantidad = 1;
  imagenSeleccionada: any = null;
  loading = true;
  esShort = false; // Flag para determinar descuento
  agregandoAlCarrito = false;
  coloresDisponibles: any[] = [];
  colorSeleccionado: any = null;
  subcategorias: any[] = [];
  categoriesMap = new Map<number, any>();
  zoomOrigin = 'center center';


  // ✅ FIX: Add Subject for cleanup
  private destroy$ = new Subject<void>();

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private apiService: ApiService,
    private cartService: CartService,
    private seoService: SeoService,
    private cdr: ChangeDetectorRef,
    private zone: NgZone
  ) { }

  ngOnInit() {
    // ✅ FIX: Subscribe to params changes to handle component reuse
    this.route.paramMap
      .pipe(takeUntil(this.destroy$))
      .subscribe(params => {
        const id = params.get('id');
        if (id) {
          this.loadProducto(+id);
        }
      });

    // Load static data once
    this.loadTalles();
    this.loadColores();
  }

  ngOnDestroy() {
    // ✅ FIX: Complete the destroy subject
    this.destroy$.next();
    this.destroy$.complete();

    // Clean up structured data when leaving the page
    this.seoService.removeStructuredData('Product');
  }

  loadProducto(id: number) {
    this.loading = true;

    this.apiService.getProducto(id).subscribe({
      next: (data) => {
        this.zone.run(() => {
          this.producto = data;
          if (data.imagenes && data.imagenes.length > 0) {
            this.imagenSeleccionada = data.imagenes.find((img: any) => img.es_principal) || data.imagenes[0];
          }
          // Filter XS from product stock if backend returned it
          if (data.stock_talles) {
            data.stock_talles = data.stock_talles.filter((st: any) => st.talle_nombre !== 'XS');
          }

          // Update SEO meta tags
          this.updateSeoTags();

          // Cargar colores disponibles para este producto
          this.loadColoresDisponibles();

          // Auto-seleccionar primer talle con stock
          this.autoSeleccionarTalle();

          // Cargar subcategorías y chequear descuento (recursive)
          this.loadSubcategorias();

          this.loading = false;
          this.cdr.detectChanges();
        });
      },
      error: (error) => {
        console.error('Error cargando producto:', error);
        this.zone.run(() => {
          this.loading = false;
          this.cdr.detectChanges();
        });
      }
    });
  }

  private autoSeleccionarTalle() {
    /* Auto-select disabled per user request
    if (this.producto && this.producto.stock_talles && this.talles.length > 0) {
      // Intentar encontrar el primer talle que tenga stock real
      const talleConStock = this.talles.find(t => this.tieneStockTalle(t.id));
      if (talleConStock) {
        this.talleSeleccionado = talleConStock;
        this.cantidad = 1;
      }
    }
    */
  }

  private updateSeoTags() {
    if (!this.producto) return;

    const apiBase = this.apiService.getApiUrl().replace('/api', '');
    const imageUrl = this.producto.imagenes && this.producto.imagenes.length > 0
      ? `${apiBase}${this.producto.imagenes[0].url}`
      : 'https://elvestuario-r4.com.ar/assets/logo.png';

    // Update meta tags
    this.seoService.updateMetaTags({
      title: this.producto.nombre,
      description: this.producto.descripcion || `${this.producto.nombre} - El Vestuario`,
      image: imageUrl,
      url: window.location.href,
      type: 'product'
    });

    // Add Product structured data
    const productSchema = this.seoService.generateProductSchema(this.producto);
    this.seoService.addStructuredData(productSchema);

    // Add breadcrumb structured data
    const breadcrumbs = [
      { name: 'Inicio', url: 'https://elvestuario-r4.com.ar/' },
      { name: 'Productos', url: 'https://elvestuario-r4.com.ar/productos' },
      { name: this.producto.nombre, url: window.location.href }
    ];
    const breadcrumbSchema = this.seoService.generateBreadcrumbSchema(breadcrumbs);
    this.seoService.addStructuredData(breadcrumbSchema);

    // Set canonical URL
    this.seoService.setCanonicalUrl(window.location.href);
  }

  loadTalles() {
    this.apiService.getTalles().subscribe({
      next: (data) => {
        this.zone.run(() => {
          this.talles = data.filter((t: any) => t.nombre !== 'XS');
          this.autoSeleccionarTalle(); // Re-intentar si el producto ya cargó
          this.cdr.detectChanges();
        });
      },
      error: (error) => {
        console.error('Error cargando talles:', error);
      }
    });
  }

  seleccionarTalle(talle: any) {
    if (this.getStockTalle(talle.id) > 0) {
      this.talleSeleccionado = talle;
    }
  }

  getStockTalle(talleId: number): number {
    if (!this.producto || !this.producto.stock_talles) return 0;
    // Use loose equality to match string/number IDs
    const stock = this.producto.stock_talles.find((s: any) => s.talle_id == talleId);
    return stock ? stock.cantidad : 0;
  }

  tieneStockTalle(talleId: number): boolean {
    return this.getStockTalle(talleId) > 0;
  }

  cambiarImagen(imagen: any) {
    this.imagenSeleccionada = imagen;
  }

  agregarAlCarrito() {
    console.log('addCart click. Selected:', this.talleSeleccionado, 'Cant:', this.cantidad);

    if (!this.producto.tiene_stock) {
      alert('Este producto no tiene stock disponible.');
      return;
    }

    if (!this.talleSeleccionado) {
      alert('Por favor selecciona un talle');
      return;
    }

    const stock = this.getStockTalle(this.talleSeleccionado.id);
    if (this.cantidad > stock) {
      alert(`No hay suficiente stock. Disponibles: ${stock}`);
      return;
    }

    this.agregandoAlCarrito = true;
    this.cartService.addItem(this.producto, this.talleSeleccionado, this.cantidad);

    // Reducir tiempo de feedback visual
    setTimeout(() => {
      this.agregandoAlCarrito = false;
      this.cdr.detectChanges(); // Force update
    }, 500);
  }

  getImagenUrl(imagen: any): string {
    if (!imagen || !imagen.url) {
      return 'assets/logo.png'; // Fallback to logo or placeholder
    }
    const apiBase = this.apiService.getApiUrl().replace('/api', '');
    return `${apiBase}${imagen.url}`;
  }

  aumentarCantidad() {
    if (this.talleSeleccionado) {
      const stock = this.getStockTalle(this.talleSeleccionado.id);
      if (this.cantidad < stock) {
        this.cantidad++;
      }
    }
  }

  disminuirCantidad() {
    if (this.cantidad > 1) {
      this.cantidad--;
    }
  }

  getPrecioConDescuento(): number {
    const final = this.getPrecioFinal();
    if (!final) return 0;

    // Shorts (ID 8) o descendientes tienen 10% descuento, el resto 15%
    const porcentaje = this.esShort ? 0.90 : 0.85;
    return final * porcentaje;
  }

  getTransferenciaDiscountText(): string {
    if (this.esShort) {
      return '¡10% OFF!';
    }
    return '¡15% OFF!';
  }

  getPrecioCuotas(): number {
    const final = this.getPrecioFinal();
    return final ? final / 3 : 0;
  }

  // Obtener el mejor precio disponible (base, descuento directo o promoción)
  getPrecioFinal(): number {
    if (!this.producto) return 0;
    let mejorPrecio = this.producto.precio_descuento || this.producto.precio_base || 0;

    if (this.producto.promociones && this.producto.promociones.length > 0) {
      const promo = this.producto.promociones[0];
      const tipo = (promo.tipo_promocion_nombre || '').toLowerCase();
      const valor = promo.valor || 0;

      if (tipo.includes('porcentaje')) {
        const precioPromo = (this.producto.precio_base || 0) * (1 - (valor / 100));
        if (precioPromo < mejorPrecio) mejorPrecio = precioPromo;
      } else if (tipo.includes('fijo')) {
        const precioPromo = Math.max(0, (this.producto.precio_base || 0) - valor);
        if (precioPromo < mejorPrecio) mejorPrecio = precioPromo;
      }
    }

    return mejorPrecio;
  }

  getPorcentajeDescuento(): number {
    if (!this.producto) return 0;
    const precioBase = this.producto.precio_base;
    const precioFinal = this.getPrecioFinal();

    if (!precioBase || precioFinal >= precioBase) return 0;
    return Math.round((1 - (precioFinal / precioBase)) * 100);
  }

  // Obtener texto para el badge de promoción
  getBadgeText(): string {
    if (!this.producto || !this.producto.promociones || this.producto.promociones.length === 0) return '';
    const promo = this.producto.promociones[0];
    if (!promo) return '';
    const tipo = (promo.tipo_promocion_nombre || '').toLowerCase();

    if (tipo.includes('porcentaje')) return `${promo.valor || 0}% OFF`;
    if (tipo.includes('fijo')) return `$${promo.valor || 0} OFF`;
    if (tipo.includes('2x1')) return '2x1';
    if (tipo.includes('3x2')) return '3x2';

    return promo.tipo_promocion_nombre || '';
  }

  loadColores() {
    this.apiService.getColores().subscribe({
      next: (data) => {
        // Los colores se cargarán cuando se cargue el producto
      },
      error: (error) => {
        console.error('Error cargando colores:', error);
      }
    });
  }

  cambiarColor(colorProducto: any) {
    // Navegar al producto del color seleccionado
    if (colorProducto.id && colorProducto.id !== this.producto.id) {
      this.router.navigate(['/productos', colorProducto.id]);
    }
  }

  loadColoresDisponibles() {
    if (!this.producto) return;

    // Obtener colores únicos del stock de este producto
    const coloresMap = new Map();
    if (this.producto.stock_talles) {
      this.producto.stock_talles.forEach((stock: any) => {
        if (stock.color_id && stock.color_nombre) {
          if (!coloresMap.has(stock.color_id)) {
            coloresMap.set(stock.color_id, {
              id: stock.color_id,
              nombre: stock.color_nombre,
              codigo_hex: null // Se puede obtener del API si está disponible
            });
          }
        }
      });
    }

    this.coloresDisponibles = Array.from(coloresMap.values());

    // Cargar información completa de colores desde el API
    this.apiService.getColores().subscribe({
      next: (colores) => {
        this.coloresDisponibles = this.coloresDisponibles.map(color => {
          const colorCompleto = colores.find((c: any) => c.id === color.id);
          return colorCompleto || color;
        });
      }
    });
  }



  buildCategoriesMap(nodes: any[]) {
    nodes.forEach(node => {
      this.categoriesMap.set(node.id, node);
      if (node.subcategorias && node.subcategorias.length > 0) {
        this.buildCategoriesMap(node.subcategorias);
      }
    });
  }

  loadSubcategorias() {
    if (!this.producto) return;

    // Obtener la categoría padre del producto actual
    this.apiService.getCategorias().subscribe({
      next: (categorias) => {
        // Flatten the tree
        this.buildCategoriesMap(categorias);

        // Chequear si es Short (recursivo) usando el MAPA
        let currentId = +this.producto.categoria_id;
        let attempts = 0;
        this.esShort = false;

        while (currentId && attempts < 10) {
          // Check ID 8 (Local) or 2 (Prod) or Name
          if (currentId === 8 || currentId === 2) {
            this.esShort = true;
            break;
          }
          const cat = this.categoriesMap.get(currentId);
          if (cat) {
            if (cat.nombre && cat.nombre.toLowerCase().trim() === 'shorts') {
              this.esShort = true;
              break;
            }
            if (cat.categoria_padre_id) {
              currentId = +cat.categoria_padre_id;
            } else {
              break;
            }
          } else {
            break;
          }
          attempts++;
        }

        const categoriaActual = this.categoriesMap.get(this.producto.categoria_id);
        if (categoriaActual && categoriaActual.categoria_padre_id) {
          // El producto está en una subcategoría. Obtener siblings.
          const parent = this.categoriesMap.get(categoriaActual.categoria_padre_id);
          this.subcategorias = parent ? (parent.subcategorias || []) : [];
        } else if (categoriaActual && !categoriaActual.categoria_padre_id) {
          // El producto está en una categoría raiz.
          this.subcategorias = categoriaActual.subcategorias || [];
        }
      }
    });
  }

  onMouseMove(e: MouseEvent) {
    const target = e.currentTarget as HTMLElement;
    const { left, top, width, height } = target.getBoundingClientRect();
    const x = ((e.clientX - left) / width) * 100;
    const y = ((e.clientY - top) / height) * 100;
    this.zoomOrigin = `${x}% ${y}%`;
  }

  onMouseLeave() {
    this.zoomOrigin = 'center center';
  }
}
