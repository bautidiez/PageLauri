import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { CheckoutService } from '../../services/checkout.service';
import { AuthService } from '../../services/auth.service';

@Component({
    selector: 'app-mis-pedidos',
    standalone: true,
    imports: [CommonModule, FormsModule],
    templateUrl: './mis-pedidos.html',
    styleUrl: './mis-pedidos.css'
})
export class MisPedidosComponent {
    email: string = '';
    pedidos: any[] = [];
    loading = false;
    searched = false;
    pedidoDetalle: any = null;

    constructor(private checkoutService: CheckoutService, private authService: AuthService) {
        const cliente = this.authService.getCliente();
        if (cliente && cliente.email) {
            this.email = cliente.email;
            this.buscar(); // Auto search if logged in
        }
    }

    buscar() {
        if (!this.email) return;
        this.loading = true;
        this.checkoutService.getPedidosCliente(this.email).subscribe({
            next: (data) => {
                this.pedidos = data;
                this.loading = false;
                this.searched = true;
            },
            error: () => {
                this.loading = false;
                this.searched = true;
            }
        });
    }

    verDetalle(pedido: any) {
        this.pedidoDetalle = pedido;
    }

    cerrarDetalle() {
        this.pedidoDetalle = null;
    }

    getEstadoColor(estado: string): string {
        const colores: any = {
            'pendiente': '#ed8936',
            'pagado': '#48bb78',
            'preparando': '#4299e1',
            'enviado': '#9f7aea',
            'entregado': '#2f855a',
            'cancelado': '#e53e3e'
        };
        return colores[estado.toLowerCase()] || '#718096';
    }
    getTrackingUrl(transportista: string, guia: string): string | null {
        if (!guia) return null;
        const t = transportista.toLowerCase();

        if (t.includes('andreani')) {
            return `https://segui-tu-envio.andreani.com/?seguimiento=${guia}`;
        }
        if (t.includes('correo')) {
            return `https://www.correoargentino.com.ar/formularios/e-commerce?id=${guia}`;
        }
        return null;
    }
}
