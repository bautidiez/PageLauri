import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable } from 'rxjs';
import { AuthService } from './auth.service';
import { ApiService } from './api.service';
import { ToastService } from './toast.service';

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
    private apiService: ApiService,
    private toastService: ToastService
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
    console.log('DEBUG CART: Adding item', { productoId: producto.id, talleId: talle.id, cantidad });

    // Validar Stock
    // Use loose comparison for IDs to avoid string/number mismatch
    const stockEntry = producto.stock_talles?.find((s: any) => s.talle_id == talle.id);
    const stockDisponible = stockEntry?.cantidad || 0;

    console.log('DEBUG CART: Stock disponible:', stockDisponible);

    // Calcular cantidad actual en carrito
    const existingIndex = this.cartItems.findIndex(
      item => item.producto.id == producto.id && item.talle.id == talle.id
    );

    const currentQty = existingIndex >= 0 ? this.cartItems[existingIndex].cantidad : 0;
    const newTotal = currentQty + cantidad;

    if (newTotal > stockDisponible) {
      console.warn(`DEBUG CART: Stock insuficiente. Disp: ${stockDisponible}, Curr: ${currentQty}, Req: ${cantidad}`);
      this.toastService.show(`No hay suficiente stock. Disponibles: ${stockDisponible}, ya tienes: ${currentQty} en carrito.`, 'error');
      return;
    }

    // Always use precio_base as the reference unit price for the cart line.
    // Discounts (static or dynamic) will be calculated in calculateTotal()
    const precio = producto.precio_base;

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

    // 1. Calculate Total Quantity for Global Discount
    const totalQty = this.getItemCount();
    let globalQtyDiscountPercent = 0;

    if (totalQty >= 3) {
      globalQtyDiscountPercent = 15;
    } else if (totalQty === 2) {
      globalQtyDiscountPercent = 10;
    }

    // Group items by promotion
    const itemsPorPromocion: { [key: string]: CartItem[] } = {};
    const itemsSinPromocionDinamica: CartItem[] = [];

    this.cartItems.forEach(item => {
      // Calculate Global Quantity Discount per item (Additive)
      const basePrice = item.producto.precio_base || 0;
      // Static Price is the basis for most discounts
      const staticPrice = item.producto.precio_descuento && item.producto.precio_descuento > 0
        ? item.producto.precio_descuento
        : basePrice;

      if (globalQtyDiscountPercent > 0) {
        const qtyDiscountAmount = staticPrice * item.cantidad * (globalQtyDiscountPercent / 100);
        item.descuento = (item.descuento || 0) + qtyDiscountAmount;
        // We will subtract this from the total later or strictly implicitly via net price
        // Actually, easiest is to sum up 'final prices' minus 'global discount'
      }

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

    // 2. Calcular items sin promoción DINÁMICA (solo checkear precio_descuento estático)
    itemsSinPromocionDinamica.forEach(item => {
      const basePrice = item.producto.precio_base || 0;
      const staticPrice = item.producto.precio_descuento && item.producto.precio_descuento > 0
        ? item.producto.precio_descuento
        : basePrice;

      // Item discount already has global qty discount added above
      // Add static discount (Base - Static)
      item.descuento = (item.descuento || 0) + ((basePrice - staticPrice) * item.cantidad);

      // Total contribution is StaticPrice * Qty - GlobalDiscount
      const globalDesc = staticPrice * item.cantidad * (globalQtyDiscountPercent / 100);
      total += (staticPrice * item.cantidad) - globalDesc;
    });

    // 3. Calcular items con promoción DINÁMICA agrupada
    Object.values(itemsPorPromocion).forEach(group => {
      // Assuming all items in group have same promo type
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

          // Calculate Promo Discount contribution (Base - Final)
          const promoDesc = (basePrice - finalPrice) * item.cantidad;
          item.descuento = (item.descuento || 0) + promoDesc;

          // Total contribution: FinalPrice * Qty - GlobalDiscount (applied on static price)
          // Wait, backend applies qty discount on 'precio_unitario' (static price)
          // So we should subtract that amount regardless of whether we chose dynamic price?
          // Backend Logic: item['descuento_aplicado'] += amount (qty)
          // Then loops promos...
          // If promo 'porcentaje' -> item['descuento_aplicado'] += discount
          // So discounts ACUMULATE.
          // Frontend 'total' should be: (Base * Qty) - TotalDiscount.
          // Or (FinalPriceFromBestPromo * Qty) - QtyDiscount?
          // If we accumulate discounts using Base as reference:

          // Re-aligning with Backend Additive Logic:
          // Qty Discount = Static * Qty * %
          // Promo Discount = Base * Qty * % (if percentage)
          // Static Discount = (Base - Static) * Qty

          // The Frontend Logic used 'finalPrice' = min(Static, Dynamic).
          // Meaning it chooses the better DEAL. 
          // If Dynamic is better, we use Dynamic.
          // THEN we subtract Qty Discount (which is additive).

          const globalDesc = staticPrice * item.cantidad * (globalQtyDiscountPercent / 100);
          total += (finalPrice * item.cantidad) - globalDesc;
        });
      }
      // Cantidad (2x1, 3x2)
      else if (tipo.includes('2x1') || tipo.includes('3x2')) {
        let slots: { price: number, parentItem: CartItem }[] = [];
        group.forEach(item => {
          // Use Base Price for 2x1 slots logic usually? Backend uses 'precio_unitario' (Static)
          // Backend line 105: {'precio': item['precio_unitario']...}
          // So slots use Static Price.
          const p = item.producto.precio_descuento || item.producto.precio_base;
          for (let i = 0; i < item.cantidad; i++) {
            slots.push({ price: p, parentItem: item });
          }
        });

        slots.sort((a, b) => b.price - a.price);
        const factor = tipo.includes('2x1') ? 2 : 3;

        let groupTotal = 0;
        slots.forEach((slot, i) => {
          if ((i + 1) % factor === 0) {
            // Item gratis (100% off this slot)
            slot.parentItem.descuento = (slot.parentItem.descuento || 0) + slot.price;
          } else {
            groupTotal += slot.price;
          }
        });

        // Additive Global Discount
        // Backend applies Global Discount to ALL items regardless of 2x1 status
        // So we subtract Global Discount for ALL items in this group
        let totalGlobalDescForGroup = 0;
        group.forEach(item => {
          const p = item.producto.precio_descuento || item.producto.precio_base;
          totalGlobalDescForGroup += p * item.cantidad * (globalQtyDiscountPercent / 100);
        });

        total += groupTotal - totalGlobalDescForGroup;
      }
      else {
        // Fallback
        group.forEach(item => {
          const finalPrice = item.producto.precio_descuento || item.producto.precio_base;
          const globalDesc = finalPrice * item.cantidad * (globalQtyDiscountPercent / 100);

          // Add Promo Discount (Base - Final) if any? 
          // Default fallthrough assumes no meaningful dynamic promo, just static
          // item.descuento already has qty discount
          const basePrice = item.producto.precio_base || 0;
          item.descuento = (item.descuento || 0) + ((basePrice - finalPrice) * item.cantidad);

          total += (finalPrice * item.cantidad) - globalDesc;
        });
      }
    });

    return Math.max(0, total);
  }

  getItemCount(): number {
    return this.cartItems.reduce((count, item) => count + item.cantidad, 0);
  }
}

