import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../services/api.service';

@Component({
  selector: 'app-home',
  imports: [CommonModule, RouterModule, FormsModule],
  templateUrl: './home.html',
  styleUrl: './home.css'
})
export class HomeComponent implements OnInit {
  productosDestacados: any[] = [];
  productosOfertas: any[] = [];
  categorias: any[] = [];
  loading = true;
  newsletterNombre = '';
  newsletterEmail = '';

  constructor(
    private apiService: ApiService,
    private cdr: ChangeDetectorRef
  ) { }

  ngOnInit() {
    this.loadProductosDestacados();
    this.loadProductosOfertas();
    this.loadCategorias();
  }

  loadProductosDestacados() {
    this.loading = true;

    this.apiService.getProductos({ destacados: true }).subscribe({
      next: (data) => {
        // El backend ahora devuelve { items: [...], total: X }
        const productos = data.items || data;
        this.productosDestacados = productos.slice(0, 9);
        this.loading = false;

        // 🔥 FORZAR Change Detection
        this.cdr.detectChanges();
      },
      error: (error) => {
        console.error('Error cargando productos destacados:', error);
        this.loading = false;
        this.cdr.detectChanges();
      }
    });
  }

  loadProductosOfertas() {
    this.apiService.getProductos({ ofertas: true }).subscribe({
      next: (data) => {
        // El backend ahora devuelve { items: [...], total: X }
        const productos = data.items || data;

        // El backend ya filtra por ofertas (precio_descuento o promociones activas)
        // No necesitamos filtrar de nuevo aquí
        this.productosOfertas = productos.slice(0, 9);

        // 🔥 FORZAR Change Detection
        this.cdr.detectChanges();
      },
      error: (error) => {
        console.error('Error cargando productos en oferta:', error);
        this.productosOfertas = []; // Asegurar array vacío en caso de error
        this.cdr.detectChanges();
      }
    });
  }

  loadCategorias() {
    this.apiService.getCategorias().subscribe({
      next: (data) => {
        // Mostrar solo categorías padre (Remeras y Shorts)
        this.categorias = data.filter((cat: any) => !cat.categoria_padre_id);

        // 🔥 FORZAR Change Detection
        this.cdr.detectChanges();
      },
      error: (error) => {
        console.error('Error cargando categorías:', error);
        this.cdr.detectChanges();
      }
    });
  }

  getImagenPrincipal(producto: any): string {
    if (producto.imagenes && producto.imagenes.length > 0) {
      const principal = producto.imagenes.find((img: any) => img.es_principal);
      if (principal) {
        return `http://localhost:5000${principal.url}`;
      }
      return `http://localhost:5000${producto.imagenes[0].url}`;
    }
    return 'https://via.placeholder.com/300x300?text=Sin+imagen';
  }

  // Calcular precio con 15% descuento por transferencia
  getPrecioTransferencia(producto: any): number {
    const precioBase = producto.precio_descuento || producto.precio_base;
    return precioBase * 0.85; // 15% descuento
  }

  // Calcular cuota (dividir en 3 cuotas sin interés)
  getCuota(producto: any): number {
    const precioBase = producto.precio_descuento || producto.precio_base;
    return precioBase / 3;
  }

  // Verificar si un producto tiene oferta válida
  tieneOferta(producto: any): boolean {
    return (producto.precio_descuento && producto.precio_descuento > 0) ||
      (producto.promociones && producto.promociones.some((p: any) => p.esta_activa));
  }

  // Calcular porcentaje de descuento
  getPorcentajeDescuento(producto: any): number {
    if (!producto.precio_descuento || !producto.precio_base) return 0;
    return Math.round((1 - (producto.precio_descuento / producto.precio_base)) * 100);
  }

  // Getter para controlar la visibilidad de la sección de ofertas
  get mostrarSeccionOfertas(): boolean {
    return this.productosOfertas.length > 0;
  }

  suscribirNewsletter() {
    // Por ahora solo muestra un mensaje, se puede implementar backend después
    alert('¡Gracias por suscribirte! Te mantendremos informado de nuestras novedades.');
    this.newsletterNombre = '';
    this.newsletterEmail = '';
  }
}
