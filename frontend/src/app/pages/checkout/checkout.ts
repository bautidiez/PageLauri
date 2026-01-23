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
  procesando = false;

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
    this.items = this.cartService.getItems();
    if (this.items.length === 0) {
      this.router.navigate(['/carrito']);
      return;
    }

    // Auto-llenar email si el usuario está logueado
    const clienteLogueado = this.authService.getCliente();
    if (clienteLogueado && clienteLogueado.email) {
      this.cliente.email = clienteLogueado.email;
    }

    this.subtotal = this.cartService.getTotal();
    this.calcularEnvio();
    this.loadMetodosPago();
  }

  loadMetodosPago() {
    this.apiService.getMetodosPago().subscribe({
      next: (data) => {
        this.metodosPago = data;
        if (data.length > 0) {
          this.metodoPagoSeleccionado = data[0].id;
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
    this.total = this.subtotal + this.costoEnvio;
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
        alert(`Pedido creado exitosamente. Número de pedido: ${data.numero_pedido}`);
        this.router.navigate(['/']);
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
