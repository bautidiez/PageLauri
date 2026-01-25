import { Component, OnInit, HostListener, ElementRef } from '@angular/core';
import { Observable } from 'rxjs';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, RouterModule } from '@angular/router';
import { CartService } from '../../services/cart.service';
import { AuthService } from '../../services/auth.service';
import { ApiService } from '../../services/api.service';

@Component({
  selector: 'app-header',
  standalone: true,
  imports: [CommonModule, RouterModule, FormsModule],
  templateUrl: './header.html',
  styleUrl: './header.css'
})
export class HeaderComponent implements OnInit {
  categorias: any[] = [];
  categoriasTree: any[] = [];
  cartItemCount = 0;
  cartTotal$: Observable<number>; // Observable version
  isAdmin = false;
  isCliente = false;
  currentUser: any = null;
  menuOpen = false;
  isProductsMenuOpen = false;
  activeCategory: any | null = null;
  busqueda = '';

  private menuCloseTimeout: any;

  constructor(
    private router: Router,
    public cartService: CartService, // Make public for template access if needed, or use property
    private authService: AuthService,
    private apiService: ApiService,
    private el: ElementRef,
    private cdr: import('@angular/core').ChangeDetectorRef
  ) {
    this.cartTotal$ = this.cartService.total$;
  }

  ngOnInit() {
    this.loadCategorias();
    this.updateAuthState();

    this.cartService.cart$.subscribe(items => {
      this.cartItemCount = items.reduce((sum, item) => sum + (item.cantidad || 0), 0);
      // We don't need to manually set cartTotal anymore, AsyncPipe handles total$
    });

    // ... (rest of ngOnInit)

    // Suscribirse para cambios futuros
    this.authService.isAuthenticated$.subscribe(() => {
      this.updateAuthState();
    });
  }

  updateAuthState() {
    this.isAdmin = !!this.authService.getAdmin();
    this.isCliente = !!this.authService.getCliente();
    this.currentUser = this.isAdmin ? this.authService.getAdmin() : this.authService.getCliente();
  }

  loadCategorias() {
    // Cargar lista plana para otros usos
    this.apiService.getCategorias().subscribe({
      next: (data) => {
        this.categorias = data;
      },
      error: (error) => {
        console.error('Error cargando categorías:', error);
      }
    });

    // Cargar árbol para el mega-menú
    this.apiService.getCategoriasTree().subscribe({
      next: (data) => {
        this.categoriasTree = data;
        console.log('🌳 Árbol de categorías cargado:', this.categoriasTree);
      },
      error: (error) => {
        console.error('Error cargando árbol de categorías:', error);
      }
    });
  }

  // Abrir el menú de productos
  openProductsMenu() {
    this.cancelCloseProductsMenu();
    this.isProductsMenuOpen = true;
  }

  // Programar cierre del menú con delay
  scheduleCloseProductsMenu() {
    this.menuCloseTimeout = setTimeout(() => {
      this.isProductsMenuOpen = false;
      this.clearActiveCategory();
    }, 150); // 150ms de delay para evitar parpadeos, cerrar más rápido
  }

  // Cancelar cierre pendiente
  cancelCloseProductsMenu() {
    if (this.menuCloseTimeout) {
      clearTimeout(this.menuCloseTimeout);
      this.menuCloseTimeout = null;
    }
  }

  // Cerrar menú inmediatamente (al hacer click o salir del mega-menu)
  closeProductsMenuNow() {
    this.cancelCloseProductsMenu();
    this.isProductsMenuOpen = false;
    this.clearActiveCategory();
  }

  // Establecer categoría activa y mostrar sus subcategorías
  setActiveCategory(category: any) {
    this.activeCategory = category;
  }

  // Limpiar categoría activa (ocultar subcategorías)
  clearActiveCategory() {
    this.activeCategory = null;
  }

  toggleMenu() {
    this.menuOpen = !this.menuOpen;
  }

  goToCart() {
    this.router.navigate(['/carrito']);
  }

  goToAdmin() {
    if (this.isAdmin) {
      this.router.navigate(['/admin']);
    } else {
      this.router.navigate(['/admin/login']);
    }
  }

  logout() {
    this.authService.logout();
  }

  buscarProductos() {
    if (this.busqueda.trim()) {
      this.router.navigate(['/productos'], { queryParams: { busqueda: this.busqueda.trim() } });
    }
  }

  onSearchBlur() {
    // Mantener el valor del buscador si hay texto
  }

  @HostListener('document:click', ['$event'])
  onDocumentClick(event: MouseEvent) {
    if (!this.el.nativeElement.contains(event.target)) {
      this.isProductsMenuOpen = false;
      this.clearActiveCategory();
    }
  }
}
