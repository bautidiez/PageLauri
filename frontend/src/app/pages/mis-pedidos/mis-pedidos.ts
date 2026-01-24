import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterModule } from '@angular/router';
import { CheckoutService } from '../../services/checkout.service';
import { AuthService } from '../../services/auth.service';

@Component({
    selector: 'app-mis-pedidos',
    standalone: true,
    imports: [CommonModule, FormsModule, RouterModule],
    templateUrl: './mis-pedidos.html',
    styleUrl: './mis-pedidos.css'
})
export class MisPedidosComponent implements OnInit {
    // UI State
    isEditingProfile = false;
    showPasswordModal = false;

    // Profile Data
    profileData = {
        nombre: '',
        email: '',
        telefono: ''
    };
    savingProfile = false;

    // Password Data
    passwordData = {
        old: '',
        new: '',
        confirm: ''
    };
    changingPassword = false;

    // Orders Data
    pedidos: any[] = [];
    loadingOrders = false;
    pedidoDetalle: any = null;

    constructor(
        private checkoutService: CheckoutService,
        private authService: AuthService
    ) { }

    ngOnInit() {
        const cliente = this.authService.getCliente();
        if (cliente) {
            this.profileData = {
                nombre: cliente.nombre,
                email: cliente.email,
                telefono: cliente.telefono
            };
            this.loadOrders();
        }
    }

    // --- UI Helpers ---
    toggleEditMode() {
        this.isEditingProfile = !this.isEditingProfile;
    }

    togglePasswordModal() {
        this.showPasswordModal = !this.showPasswordModal;
        // Reset form when closing
        if (!this.showPasswordModal) {
            this.passwordData = { old: '', new: '', confirm: '' };
        }
    }

    // --- Profile Management ---

    saveProfile() {
        this.savingProfile = true;
        this.checkoutService.updateProfile(this.profileData).subscribe({
            next: (updatedCliente) => {
                this.authService.updateCliente(updatedCliente); // Update local storage
                alert('Perfil actualizado correctamente');
                this.savingProfile = false;
                this.isEditingProfile = false; // Return to view mode
            },
            error: (err) => {
                console.error(err);
                alert('Error al actualizar perfil');
                this.savingProfile = false;
            }
        });
    }

    changePassword() {
        if (this.passwordData.new !== this.passwordData.confirm) {
            alert('Las contraseñas nuevas no coinciden');
            return;
        }
        if (!this.passwordData.old || !this.passwordData.new) {
            alert('Por favor completá todos los campos');
            return;
        }

        this.changingPassword = true;
        this.checkoutService.changePassword({
            old_password: this.passwordData.old,
            new_password: this.passwordData.new
        }).subscribe({
            next: (res) => {
                alert(res.message);
                this.passwordData = { old: '', new: '', confirm: '' };
                this.togglePasswordModal();
                this.changingPassword = false;
            },
            error: (err) => {
                console.error(err);
                alert(err.error?.error || 'Error al cambiar contraseña');
                this.changingPassword = false;
            }
        });
    }

    // --- Orders Management ---

    loadOrders() {
        this.loadingOrders = true;
        this.checkoutService.getMyOrders().subscribe({
            next: (data) => {
                this.pedidos = data;
                this.loadingOrders = false;
            },
            error: (err) => {
                console.error(err);
                this.loadingOrders = false;
            }
        });
    }

    isCancelled(pedido: any): boolean {
        // Condition: Status is 'cancelado' (Anulado)
        if (pedido.estado === 'cancelado') return true;

        // Also check if pending approval and > 5 days (Display logic only)
        if (pedido.estado === 'pendiente_aprobacion' && pedido.created_at) {
            const created = new Date(pedido.created_at);
            const diff = new Date().getTime() - created.getTime();
            const days = diff / (1000 * 3600 * 24);
            if (days > 5) return true;
        }
        return false;
    }

    getEstadoLabel(pedido: any): string {
        if (this.isCancelled(pedido)) return 'Anulado';
        if (pedido.estado === 'entregado') return 'Finalizado';
        return pedido.estado.replace('_', ' ');
    }

    getEstadoColor(pedido: any): string {
        if (this.isCancelled(pedido)) return '#e53e3e'; // Red

        switch (pedido.estado) {
            case 'pendiente_aprobacion': return '#ed8936'; // Orange
            case 'pagado': return '#48bb78'; // Green
            case 'preparando': return '#4299e1'; // Blue
            case 'enviado': return '#9f7aea'; // Purple
            case 'entregado': return '#2f855a'; // Dark Green
            default: return '#718096'; // Gray
        }
    }

    verDetalle(pedido: any) {
        this.pedidoDetalle = pedido;
    }

    cerrarDetalle() {
        this.pedidoDetalle = null;
    }

    getTrackingUrl(transportista: string, guia: string): string | null {
        if (!guia) return null;
        const t = transportista.toLowerCase();
        if (t.includes('andreani')) return `https://segui-tu-envio.andreani.com/?seguimiento=${guia}`;
        if (t.includes('correo')) return `https://www.correoargentino.com.ar/formularios/e-commerce?id=${guia}`;
        return null;
    }
}
