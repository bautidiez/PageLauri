import { Component, OnInit, OnDestroy, ChangeDetectorRef } from '@angular/core';
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
  agregandoAlCarrito = false;
  coloresDisponibles: any[] = [];
  colorSeleccionado: any = null;
  subcategorias: any[] = [];

  // ✅ FIX: Add Subject for cleanup
  private destroy$ = new Subject<void>();

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private apiService: ApiService,
    private cartService: CartService,
    private seoService: SeoService,
    private cdr: ChangeDetectorRef
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
    this.loadSubcategorias();
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
        this.producto = data;
        if (data.imagenes && data.imagenes.length > 0) {
          this.imagenSeleccionada = data.imagenes.find((img: any) => img.es_principal) || data.imagenes[0];
        }

        // Update SEO meta tags
        this.updateSeoTags();

        // Cargar colores disponibles para este producto
        this.loadColoresDisponibles();
        this.loading = false;

        // 🔥 FORZAR Change Detection
        this.cdr.detectChanges();
      },
      error: (error) => {
        console.error('Error cargando producto:', error);
        this.loading = false;
        this.cdr.detectChanges();
      }
    });
  }

  private updateSeoTags() {
    if (!this.producto) return;

    const apiBase = this.apiService.getApiUrl().replace('/api', '');
    const imageUrl = this.producto.imagenes && this.producto.imagenes.length > 0
      ? `${apiBase}${this.producto.imagenes[0].url}`
      : 'https://elvestuario-r4.vercel.app/assets/logo.png';

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
      { name: 'Inicio', url: 'https://elvestuario-r4.vercel.app/' },
      { name: 'Productos', url: 'https://elvestuario-r4.vercel.app/productos' },
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
        this.talles = data;
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
    const stock = this.producto.stock_talles.find((s: any) => s.talle_id === talleId);
    return stock ? stock.cantidad : 0;
  }

  tieneStockTalle(talleId: number): boolean {
    return this.getStockTalle(talleId) > 0;
  }

  cambiarImagen(imagen: any) {
    this.imagenSeleccionada = imagen;
  }

  agregarAlCarrito() {
    if (!this.talleSeleccionado) {
      alert('Por favor selecciona un talle');
      return;
    }

    if (this.cantidad > this.getStockTalle(this.talleSeleccionado.id)) {
      alert('No hay suficiente stock disponible');
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
    return this.getPrecioFinal() * 0.85; // 15% de descuento sobre el mejor precio
  }

  getPrecioCuotas(): number {
    return this.getPrecioFinal() / 3; // 3 cuotas sin interés
  }

  // Obtener el mejor precio disponible (base, descuento directo o promoción)
  getPrecioFinal(): number {
    if (!this.producto) return 0;
    let mejorPrecio = this.producto.precio_descuento || this.producto.precio_base;

    if (this.producto.promociones && this.producto.promociones.length > 0) {
      const promo = this.producto.promociones[0];
      const tipo = (promo.tipo_promocion_nombre || '').toLowerCase();
      const valor = promo.valor || 0;

      if (tipo.includes('porcentaje')) {
        const precioPromo = this.producto.precio_base * (1 - (valor / 100));
        if (precioPromo < mejorPrecio) mejorPrecio = precioPromo;
      } else if (tipo.includes('fijo')) {
        const precioPromo = Math.max(0, this.producto.precio_base - valor);
        if (precioPromo < mejorPrecio) mejorPrecio = precioPromo;
      }
    }

    return mejorPrecio;
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


  loadSubcategorias() {
    if (!this.producto) return;

    // Obtener la categoría padre del producto actual
    this.apiService.getCategorias().subscribe({
      next: (categorias) => {
        const categoriaActual = categorias.find((c: any) => c.id === this.producto.categoria_id);
        if (categoriaActual && categoriaActual.categoria_padre_id) {
          // El producto está en una subcategoría, obtener todas las subcategorías del mismo padre
          this.subcategorias = categorias.filter((c: any) =>
            c.categoria_padre_id === categoriaActual.categoria_padre_id
          );
        } else if (categoriaActual && !categoriaActual.categoria_padre_id) {
          // El producto está en una categoría padre, obtener todas sus subcategorías
          this.subcategorias = categorias.filter((c: any) =>
            c.categoria_padre_id === categoriaActual.id
          );
        }
      }
    });
  }
}
