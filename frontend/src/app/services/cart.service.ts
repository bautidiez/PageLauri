import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable } from 'rxjs';
import { AuthService } from './auth.service';
import { ApiService } from './api.service';

export interface CartItem {
  producto: any;
  talle: any;
  cantidad: number;
  precio_unitario: number;
  descuento?: number;
}

interface CartStorage {
  items: CartItem[];
  lastUpdated: number;
}

@Injectable({
  providedIn: 'root'
})
export class CartService {
  private cartItems: CartItem[] = [];
  private cartSubject = new BehaviorSubject<CartItem[]>([]);
  public cart$ = this.cartSubject.asObservable();

  private totalSubject = new BehaviorSubject<number>(0);
  public total$ = this.totalSubject.asObservable();

  // Constantes de tiempo
  private readonly CART_EXPIRATION = 48 * 60 * 60 * 1000; // 48 horas según pedido

  constructor(
    private authService: AuthService,
    private apiService: ApiService
  ) {
    this.initCart();
  }

  private initCart(): void {
    // Suscribirse a cambios de autenticación para recargar y FUSIONAR si es necesario
    this.authService.isAuthenticated$.subscribe((isAuth) => {
      if (isAuth) {
        this.mergeGuestCart();
      }
      this.loadCart();
    });
  }

  private getCartKey(): string {
    const cliente = this.authService.getCliente();
    if (this.authService.isLoggedIn() && cliente && cliente.id) {
      return `cart_client_${cliente.id}`;
    }
    return 'cart_guest';
  }

  public getCartItems() {
    return this.cartSubject.value;
  }

  private loadCart(): void {
    const key = this.getCartKey();
    const saved = localStorage.getItem(key);

    this.cartItems = []; // Reset inicial

    if (saved) {
      try {
        const parsed: CartStorage | CartItem[] = JSON.parse(saved);
        let items: CartItem[] = [];
        let lastUpdated = 0;

        if (Array.isArray(parsed)) {
          items = parsed;
          lastUpdated = Date.now();
        } else {
          items = parsed.items || [];
          lastUpdated = parsed.lastUpdated || 0;
        }

        // Verificar expiración (48 horas)
        const now = Date.now();
        if (now - lastUpdated > this.CART_EXPIRATION) {
          console.log(`Carrito expirado (${key}). Limpiando.`);
          this.clearCart();
          return;
        } else {
          this.cartItems = items;
          // Calculate initial total
          this.updateTotal();
          // Refresh data to get latest promotions/prices
          this.refreshCartData();
        }
      } catch (e) {
        console.error('Error al cargar carrito', e);
        this.cartItems = [];
      }
    }

    this.notify();
  }

  private refreshCartData() {
    if (this.cartItems.length === 0) return;

    // Create a list of observables or a batch request
    // For simplicity and to avoid race conditions with local state, we'll update one by one or forkJoin
    // But since we don't have forkJoin imported, let's just iterate. 
    // Ideally, backend should support batch get.

    this.cartItems.forEach((item, index) => {
      this.apiService.getProducto(item.producto.id).subscribe({
        next: (freshProduct) => {
          // Update product data (includes fresh promotions)
          this.cartItems[index].producto = freshProduct;

          // Always use precio_base as the reference unit price for the cart line.
          // Discounts (static or dynamic) will be calculated in calculateTotal()
          this.cartItems[index].precio_unitario = freshProduct.precio_base;

          console.log(`DEBUG CART: Updated item ${item.producto.nombre}. Base Price: ${freshProduct.precio_base}. Promos:`, freshProduct.promociones?.length);

          // Filter XS from product stock if backend returned it
          if (freshProduct.stock_talles) {
            this.cartItems[index].producto.stock_talles = freshProduct.stock_talles.filter((st: any) => st.talle_nombre !== 'XS');
          }

          // Trigger save to recalculate totals and notify subscribers
          this.saveCart();
        },
        error: (err) => {
          console.error(`Error refreshing product ${item.producto.id}:`, err);
          // If 404/inactive, maybe remove from cart?
          // For now, keep as is or mark as unavailable.
        }
      });
    });
  }

  private mergeGuestCart(): void {
    const guestData = localStorage.getItem('cart_guest');
    if (!guestData) return;

    try {
      const parsed: CartStorage | CartItem[] = JSON.parse(guestData);
      const guestItems = Array.isArray(parsed) ? parsed : (parsed.items || []);

      if (guestItems.length === 0) return;

      // Cargar carrito del usuario actual para fusionar
      const userKey = this.getCartKey();
      const userData = localStorage.getItem(userKey);
      let userItems: CartItem[] = [];

      if (userData) {
        const parsedUser: CartStorage | CartItem[] = JSON.parse(userData);
        userItems = Array.isArray(parsedUser) ? parsedUser : (parsedUser.items || []);
      }

      // Fusionar items
      guestItems.forEach((gItem: CartItem) => {
        const existingIndex = userItems.findIndex(
          uItem => uItem.producto.id === gItem.producto.id && uItem.talle.id === gItem.talle.id
        );

        if (existingIndex >= 0) {
          userItems[existingIndex].cantidad += gItem.cantidad;
        } else {
          userItems.push(gItem);
        }
      });

      // Guardar carrito fusionado
      this.cartItems = userItems;
      this.saveCart();

      // Limpiar carrito de invitado
      localStorage.removeItem('cart_guest');
      console.log('DEBUG CART: Carrito de invitado fusionado con el de usuario.');

    } catch (e) {
      console.error('Error al fusionar carrito de invitado', e);
    }
  }

  private notify() {
    this.updateTotal(); // Calculate first
    this.cartSubject.next(this.cartItems);
  }

  private updateTotal() {
    const total = this.calculateTotal();
    this.totalSubject.next(total);
  }

  private saveCart(): void {
    const key = this.getCartKey();
    const storageData: CartStorage = {
      items: this.cartItems,
      lastUpdated: Date.now()
    };
    localStorage.setItem(key, JSON.stringify(storageData));
    this.notify();
  }

  addItem(producto: any, talle: any, cantidad: number): void {
    // Always use precio_base as the reference unit price for the cart line.
    // Discounts (static or dynamic) will be calculated in calculateTotal()
    const precio = producto.precio_base;
    const existingIndex = this.cartItems.findIndex(
      item => item.producto.id === producto.id && item.talle.id === talle.id
    );

    if (existingIndex >= 0) {
      this.cartItems[existingIndex].cantidad += cantidad;
    } else {
      this.cartItems.push({
        producto,
        talle,
        cantidad,
        precio_unitario: precio
      });
    }

    this.saveCart();
  }

  removeItem(index: number): void {
    this.cartItems.splice(index, 1);
    this.saveCart();
  }

  updateQuantity(index: number, cantidad: number): void {
    if (cantidad > 0) {
      this.cartItems[index].cantidad = cantidad;
      this.saveCart();
    }
  }

  clearCart(): void {
    this.cartItems = [];
    const key = this.getCartKey();
    localStorage.removeItem(key); // O guardar vacío: localStorage.setItem(key, JSON.stringify({items: [], lastUpdated: Date.now()}));
    // Remover item es más limpio para "no tener nada"
    this.notify();
  }

  getItems(): CartItem[] {
    return this.cartItems;
  }

  getTotal(): number {
    return this.totalSubject.getValue();
  }

  private calculateTotal(): number {
    let total = 0;

    // Reset discounts first
    this.cartItems.forEach(item => item.descuento = 0);

    // Group items by promotion
    const itemsPorPromocion: { [key: string]: CartItem[] } = {};
    const itemsSinPromocionDinamica: CartItem[] = [];

    this.cartItems.forEach(item => {
      if (item.producto.promociones && item.producto.promociones.length > 0) {
        // En esta tienda, usualmente hay una promo principal por producto (ej: 2x1 o 15% OFF)
        const promo = item.producto.promociones[0];
        const key = promo.id ? `promo_${promo.id}` : `type_${promo.tipo_promocion_nombre}`;

        if (!itemsPorPromocion[key]) {
          itemsPorPromocion[key] = [];
        }
        itemsPorPromocion[key].push(item);
      } else {
        itemsSinPromocionDinamica.push(item);
      }
    });

    // 1. Calcular items sin promoción DINÁMICA (solo checkear precio_descuento estático)
    itemsSinPromocionDinamica.forEach(item => {
      const basePrice = item.producto.precio_base || 0;
      const staticPrice = item.producto.precio_descuento && item.producto.precio_descuento > 0
        ? item.producto.precio_descuento
        : basePrice;

      item.descuento = (basePrice - staticPrice) * item.cantidad;
      total += (staticPrice * item.cantidad);
    });

    // 2. Calcular items con promoción DINÁMICA agrupada
    Object.values(itemsPorPromocion).forEach(group => {
      const promo = group[0].producto.promociones[0];
      const tipo = (promo.tipo_promocion_nombre || '').toLowerCase();
      const valor = promo.valor || 0;

      // Porcentaje o Fijo (se aplican por unidad, competimos con precio_descuento)
      if (tipo.includes('porcentaje') || tipo.includes('fijo')) {
        group.forEach(item => {
          const basePrice = item.producto.precio_base || 0;
          const staticPrice = item.producto.precio_descuento && item.producto.precio_descuento > 0
            ? item.producto.precio_descuento
            : basePrice;

          let dynamicPrice = basePrice;
          if (tipo.includes('porcentaje')) {
            dynamicPrice = basePrice * (1 - (valor / 100));
          } else {
            dynamicPrice = Math.max(0, basePrice - valor);
          }

          // Elegir el MEJOR precio (match lógica producto-detail)
          const finalPrice = Math.min(staticPrice, dynamicPrice);
          item.descuento = (basePrice - finalPrice) * item.cantidad;
          total += (finalPrice * item.cantidad);
        });
      }
      // Cantidad (2x1, 3x2) - Usualmente no se acumulan con precio_descuento, usamos basePrice
      else if (tipo.includes('2x1') || tipo.includes('3x2')) {
        let slots: { price: number, parentItem: CartItem }[] = [];
        group.forEach(item => {
          for (let i = 0; i < item.cantidad; i++) {
            slots.push({ price: item.producto.precio_base, parentItem: item });
          }
        });

        // Ordenar por precio desc (pagas los más caros)
        slots.sort((a, b) => b.price - a.price);
        const factor = tipo.includes('2x1') ? 2 : 3;

        let groupTotal = 0;
        slots.forEach((slot, i) => {
          if ((i + 1) % factor === 0) {
            // Item gratis
            slot.parentItem.descuento = (slot.parentItem.descuento || 0) + slot.price;
          } else {
            groupTotal += slot.price;
          }
        });
        total += groupTotal;
      }
      else {
        // Fallback: usar precio_descuento o base
        group.forEach(item => {
          const finalPrice = item.producto.precio_descuento || item.producto.precio_base;
          total += finalPrice * item.cantidad;
        });
      }
    });

    return total;
  }

  getItemCount(): number {
    return this.cartItems.reduce((count, item) => count + item.cantidad, 0);
  }
}

