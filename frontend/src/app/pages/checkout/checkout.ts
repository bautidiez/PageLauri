import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { CartService } from '../../services/cart.service';
import { ApiService } from '../../services/api.service';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-checkout',
  imports: [CommonModule, FormsModule],
  templateUrl: './checkout.html',
  styleUrl: './checkout.css',
})
export class CheckoutComponent implements OnInit {
  items: any[] = [];
  metodosPago: any[] = [];
  metodoPagoSeleccionado: number | null = null;
  costoEnvio = 0;
  subtotal = 0;
  total = 0;
  descuentoPago = 0; // Descuento por método de pago
  procesando = false;
  categorias: any[] = [];
  categoriesMap = new Map<number, any>(); // Mapa para búsqueda rápida

  // Datos del cliente
  cliente = {
    nombre: '',
    email: '',
    telefono: '',
    direccion: '',
    codigo_postal: '',
    localidad: '',
    provincia: ''
  };

  metodoEnvio = 'correo_argentino';
  costosEnvio: any = {}; // Almacenar costos por método

  constructor(
    private cartService: CartService,
    private apiService: ApiService,
    private router: Router,
    private authService: AuthService
  ) { }

  ngOnInit() {
    console.log('DEBUG: CHECKOUT V1 (LEGACY) LOADED');
    this.items = this.cartService.getItems();
    if (this.items.length === 0) {
      this.router.navigate(['/carrito']);
      return;
    }

    // Auto-llenar email si el usuario está logueado
    const clienteLogueado = this.authService.getCliente();
    const adminLogueado = this.authService.getAdmin();

    if (clienteLogueado && clienteLogueado.email) {
      this.cliente.email = clienteLogueado.email;
      console.log('Email auto-filled from cliente:', this.cliente.email);
    } else if (adminLogueado && adminLogueado.email) {
      this.cliente.email = adminLogueado.email;
      console.log('Email auto-filled from admin:', this.cliente.email);
    }

    this.subtotal = this.cartService.getTotal();
    this.calcularEnvio();
    this.loadMetodosPago();
    this.loadCategorias();
  }

  loadCategorias() {
    this.apiService.getCategorias().subscribe({
      next: (data) => {
        this.categorias = data;
        this.buildCategoriesMap(data);
        this.calcularTotal(); // Recalcular con categorias cargadas
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

  checkIfShort(categoriaId: number): boolean {
    if (this.categoriesMap.size === 0) return false;

    let currentId: number | null = +categoriaId;
    let attempts = 0;

    while (currentId !== null && attempts < 10) {
      if (currentId === 8 || currentId === 2) return true;

      const category = this.categoriesMap.get(currentId);
      if (category) {
        if (category.nombre && category.nombre.toLowerCase().trim() === 'shorts') return true;

        if (category.categoria_padre_id) {
          currentId = +category.categoria_padre_id;
        } else {
          break;
        }
      } else {
        break;
      }
      attempts++;
    }
    return false;
  }

  loadMetodosPago() {
    this.apiService.getMetodosPago().subscribe({
      next: (data) => {
        this.metodosPago = data;
        if (data.length > 0) {
          this.metodoPagoSeleccionado = data[0].id;
          this.calcularTotal();
        }
      },
      error: (error) => {
        console.error('Error cargando métodos de pago:', error);
      }
    });
  }

  onCodigoPostalChange() {
    // Guardar código postal
    if (this.cliente.codigo_postal) {
      localStorage.setItem('codigo_postal', this.cliente.codigo_postal);
    }

    // Si hay código postal válido, calcular el envío para el método seleccionado
    if (this.cliente.codigo_postal && this.cliente.codigo_postal.length >= 4) {
      this.calcularEnvio();
    } else {
      this.costoEnvio = 0;
      this.calcularTotal();
    }
  }

  calcularEnvio() {
    if (this.metodoEnvio === 'retiro') {
      this.costoEnvio = 0;
      this.costosEnvio['retiro'] = 0;
      this.calcularTotal();
      return;
    }

    if (this.cliente.codigo_postal && this.cliente.codigo_postal.length >= 4) {
      const provincia = this.cliente.provincia || 'Buenos Aires';

      this.apiService.calcularEnvio({
        codigo_postal: this.cliente.codigo_postal,
        provincia: provincia,
        metodo_envio: this.metodoEnvio
      }).subscribe({
        next: (data) => {
          this.costoEnvio = data.costo || 2000;
          this.costosEnvio[this.metodoEnvio] = this.costoEnvio;
          this.calcularTotal();
        },
        error: (error) => {
          console.error('Error calculando envío:', error);
          this.costoEnvio = 2000;
          this.costosEnvio[this.metodoEnvio] = this.costoEnvio;
          this.calcularTotal();
        }
      });
    } else {
      this.costoEnvio = 0;
      this.calcularTotal();
    }
  }

  calcularTodosLosEnvios() {
    // Calcular costos para todos los métodos cuando se ingresa código postal
    if (this.cliente.codigo_postal && this.cliente.codigo_postal.length >= 4 && this.cliente.provincia) {
      const metodos = ['correo_argentino', 'andreani', 'tienda_nube'];
      metodos.forEach(metodo => {
        this.apiService.calcularEnvio({
          codigo_postal: this.cliente.codigo_postal,
          provincia: this.cliente.provincia,
          metodo_envio: metodo
        }).subscribe({
          next: (data) => {
            this.costosEnvio[metodo] = data.costo || 2000;
            if (metodo === this.metodoEnvio) {
              this.costoEnvio = this.costosEnvio[metodo];
              this.calcularTotal();
            }
          },
          error: (error) => {
            console.error(`Error calculando envío para ${metodo}:`, error);
            this.costosEnvio[metodo] = 2000;
          }
        });
      });
    }
  }

  calcularTotal() {
    this.descuentoPago = 0;

    // Calcular descuento por transferencia/efectivo
    // Logica: 10% para Shorts (y descendientes), 15% para el resto
    if (this.metodoPagoSeleccionado) {
      const metodo = this.metodosPago.find(m => m.id === this.metodoPagoSeleccionado);
      if (metodo) {
        const nombre = metodo.nombre.toLowerCase();
        if (nombre.includes('transferencia') || nombre.includes('efectivo')) {
          let totalDesc = 0;
          this.items.forEach(item => {
            // Precio base * cantidad es la base
            // Pero ojo, si tiene descuento previo promos, deberiamos usar ese?
            // Según backend: `base_pago = pedido.subtotal - pedido.descuento`.
            // Y luego aplica sobre items.
            // Simplificación frontend: Aplicar sobre el item.precio_unitario (que ya puede tener descuento estatico? NO, cartService usa precio_base)
            // CartService calculateTotal YA aplica descuentos. 
            // `item.precio_unitario` en checkout es `precio_base` segun CartService?
            // CartService: `this.cartItems[index].precio_unitario = freshProduct.precio_base;`
            // Display en resumen checkout: `item.precio_unitario * item.cantidad`.
            // PERO `subtotal` viene de `cartService.getTotal()` que tiene descuentos aplicados.
            // ESTO ES COMPLEJO. El backend aplica el 15% sobre el NETO.

            // Aproximación visual para Frontend:
            const esShort = this.checkIfShort(item.producto.categoria_id);
            const porcentaje = esShort ? 0.10 : 0.15;

            // Precio efectivo del item en el total (aproximado)
            // Si el subtotal ya tiene descuentos, es dificil prorratear. 
            // Asumiremos precio base o precio promo.

            // Mejor estrategia: Calcular sobre el monto que contribuye al subtotal?
            // CartService item.descuento tiene el descuento aplicado.

            let precioItem = item.precio_unitario; // Base
            if (item.producto.precio_descuento) precioItem = item.producto.precio_descuento;

            // Si hay promo dinamica, es mas complejo. 
            // Usaremos una heuristica: (precio * cantidad) * porcentaje
            const montoItem = precioItem * item.cantidad;
            totalDesc += montoItem * porcentaje;
          });
          this.descuentoPago = totalDesc;
        }
      }
    }

    this.total = (this.subtotal - this.descuentoPago) + this.costoEnvio;
  }

  onMetodoPagoChange() {
    this.calcularTotal();
  }

  getMetodoEnvioNombre(metodo: string): string {
    const nombres: any = {
      'correo_argentino': 'Correo Argentino',
      'andreani': 'Andreani',
      'tienda_nube': 'Tienda Nube',
      'retiro': 'Retiro en local (Gratis)'
    };
    return nombres[metodo] || metodo;
  }

  procesarPedido() {
    if (!this.validarFormulario()) {
      alert('Por favor completa todos los campos requeridos');
      return;
    }

    if (!this.metodoPagoSeleccionado) {
      alert('Por favor selecciona un método de pago');
      return;
    }

    this.procesando = true;

    const pedido = {
      cliente_nombre: this.cliente.nombre,
      cliente_email: this.cliente.email,
      cliente_telefono: this.cliente.telefono,
      cliente_direccion: this.cliente.direccion,
      cliente_codigo_postal: this.cliente.codigo_postal,
      cliente_localidad: this.cliente.localidad,
      cliente_provincia: this.cliente.provincia,
      metodo_pago_id: this.metodoPagoSeleccionado,
      metodo_envio: this.metodoEnvio,
      items: this.items.map(item => ({
        producto_id: item.producto.id,
        talle_id: item.talle.id,
        cantidad: item.cantidad
      }))
    };

    this.apiService.createPedido(pedido).subscribe({
      next: (data) => {
        this.cartService.clearCart();
        this.cartService.clearCart();
        // Removed alert, navigating to success page
        console.log('DEBUG CHECKOUT V1: Order Created, redirecting to success page.', data);
        this.router.navigate(['/pedido-exitoso'], { state: { order: data } });
      },
      error: (error) => {
        console.error('Error creando pedido:', error);
        alert('Error al procesar el pedido. Por favor intenta nuevamente.');
        this.procesando = false;
      }
    });
  }

  validarFormulario(): boolean {
    return !!(
      this.cliente.nombre &&
      this.cliente.email &&
      this.cliente.direccion &&
      this.cliente.codigo_postal &&
      this.cliente.localidad &&
      this.cliente.provincia
    );
  }
}
