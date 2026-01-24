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

  // Constantes de tiempo
  private readonly CART_EXPIRATION = 48 * 60 * 60 * 1000; // 48 horas según pedido

  constructor(
    private authService: AuthService,
    private apiService: ApiService
  ) {
    this.initCart();
  }

  // ... (previous code)

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
          // Refresh data to get latest promotions/prices
          this.refreshCartData();
        }
      } catch (e) {
        console.error('Error al cargar carrito', e);
        this.cartItems = [];
      }
    }

    this.cartSubject.next(this.cartItems);
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

          // Update base price criteria if needed, BUT preserve the logic:
          // If product has static offer (precio_descuento), use it.
          // Dynamic offers are handled in calculateTotal via item.producto.promociones

          const precio = (freshProduct.precio_descuento && freshProduct.precio_descuento > 0)
            ? freshProduct.precio_descuento
            : (freshProduct.precio_actual || freshProduct.precio_base);

          this.cartItems[index].precio_unitario = precio;

          // Filter XS if backend didn't (safety)
          if (freshProduct.stock_talles) {
            this.cartItems[index].producto.stock_talles = freshProduct.stock_talles.filter((st: any) => st.talle_nombre !== 'XS');
          }

          // Trigger save and notify only after last update? 
          // Doing it per item is chatty can cause UI jitter but ensures eventual consistency.
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

  private saveCart(): void {
    const key = this.getCartKey();
    const storageData: CartStorage = {
      items: this.cartItems,
      lastUpdated: Date.now()
    };
    localStorage.setItem(key, JSON.stringify(storageData));
    this.cartSubject.next(this.cartItems);
  }

  addItem(producto: any, talle: any, cantidad: number): void {
    // Usar precio_descuento si existe (oferta estática), sino precio_actual o base
    const precio = (producto.precio_descuento && producto.precio_descuento > 0)
      ? producto.precio_descuento
      : (producto.precio_actual || producto.precio_base);
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
    this.cartSubject.next(this.cartItems);
  }

  getItems(): CartItem[] {
    return this.cartItems;
  }

  getTotal(): number {
    return this.calculateTotal();
  }

  private calculateTotal(): number {
    let total = 0;

    // Agrupar items por tipo de promoción
    const itemsPorPromocion: { [key: string]: CartItem[] } = {};
    const itemsSinPromocion: CartItem[] = [];

    this.cartItems.forEach(item => {
      // Verificar si tiene promoción activa y válida
      if (item.producto.promociones && item.producto.promociones.length > 0) {
        const promo = item.producto.promociones[0];
        // Usar ID o nombre de la promoción para agrupar
        const key = promo.id ? `promo_${promo.id}` : `type_${promo.tipo_promocion_nombre}`;

        if (!itemsPorPromocion[key]) {
          itemsPorPromocion[key] = [];
        }
        itemsPorPromocion[key].push(item);
      } else {
        itemsSinPromocion.push(item);
      }
    });

    // Calcular items sin promoción
    itemsSinPromocion.forEach(item => {
      total += (item.precio_unitario * item.cantidad);
    });

    // Calcular items con promoción agrupada
    Object.values(itemsPorPromocion).forEach(group => {
      // Aplanar el grupo: crear una lista de precios individuales
      let prices: number[] = [];
      group.forEach(item => {
        for (let i = 0; i < item.cantidad; i++) {
          prices.push(item.precio_unitario);
        }
      });

      // Ordenar precios de mayor a menor (para descontar los más baratos)
      prices.sort((a, b) => b - a);

      // Determinar el tipo de promoción del grupo (asumimos que todos en el grupo tienen la misma)
      const promo = group[0].producto.promociones[0];
      const tipo = promo.tipo_promocion_nombre.toLowerCase();
      const valor = promo.valor || 0;

      if (tipo.includes('2x1')) {
        // Pagar 1 de cada 2 (el más caro)
        for (let i = 0; i < prices.length; i++) {
          if (i % 2 === 0) { // Indices 0, 2, 4... se pagan
            total += prices[i];
          }
        }
      } else if (tipo.includes('3x2')) {
        // Pagar 2 de cada 3
        for (let i = 0; i < prices.length; i++) {
          if ((i + 1) % 3 !== 0) { // Indices 0, 1, 3, 4... se pagan. Indices 2, 5... (cada 3ro) son gratis
            total += prices[i];
          }
        }
      } else if (tipo.includes('porcentaje')) {
        // Aplicar descuento porcentual a cada item del grupo
        prices.forEach(p => {
          total += p * (1 - (valor / 100));
        });
      } else if (tipo.includes('fijo')) {
        // Aplicar descuento fijo a cada item
        prices.forEach(p => {
          total += Math.max(0, p - valor);
        });
      } else {
        // Fallback: sumar todo
        prices.forEach(p => total += p);
      }
    });

    return total;
  }

  getItemCount(): number {
    return this.cartItems.reduce((count, item) => count + item.cantidad, 0);
  }
}

