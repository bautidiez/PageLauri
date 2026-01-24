import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
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
    currentUserEmail: string = '';

    // Debug Data
    debugInfo: any = {};
    debugError: string = '';
    debugResponse: any = null;

    constructor(
        private checkoutService: CheckoutService,
        private authService: AuthService,
        private cd: ChangeDetectorRef
    ) { }

    ngOnInit() {
        const cliente = this.authService.getCliente();
        if (cliente) {
            this.currentUserEmail = cliente.email;
            this.profileData = {
                nombre: cliente.nombre,
                email: cliente.email,
                telefono: cliente.telefono
            };

            // Populate Debug Info
            this.debugInfo = {
                cliente: cliente,
                token: localStorage.getItem('token') ? 'Presente' : 'Faltante'
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
                this.cd.detectChanges();
            },
            error: (err) => {
                console.error(err);
                alert('Error al actualizar perfil');
                this.savingProfile = false;
                this.cd.detectChanges();
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
                this.cd.detectChanges();
            },
            error: (err) => {
                console.error(err);
                alert(err.error?.error || 'Error al cambiar contraseña');
                this.changingPassword = false;
                this.cd.detectChanges();
            }
        });
    }

    // --- Orders Management ---

    loadOrders() {
        this.loadingOrders = true;
        this.debugError = '';

        this.checkoutService.getMyOrders().subscribe({
            next: (data) => {
                console.log('DEBUG: MIS PEDIDOS API DATA:', data);
                this.debugResponse = data; // Guardar respuesta raw para debug visual

                if (data.length === 0) {
                    console.log('DEBUG: No se encontraron pedidos.');
                }
                this.pedidos = data;
                this.loadingOrders = false;
                this.cd.detectChanges();
            },
            error: (err) => {
                console.error('API Error:', err);
                this.debugError = JSON.stringify(err);
                if (err.status === 401) this.debugError += ' (401 Unauthorized)';

                this.loadingOrders = false;
                this.cd.detectChanges();
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
        if (this.isCancelled(pedido)) return 'Cancelado';

        switch (pedido.estado) {
            case 'pendiente_aprobacion': return 'Revisión';
            case 'entregado': return 'Finalizado';
            // Any other state implies the admin approved it but it's not yet delivered
            case 'confirmado':
            case 'pagado':
            case 'en_preparacion':
            case 'enviado':
                return 'Aprobado';
            default: return pedido.estado.replace('_', ' ');
        }
    }

    getEstadoColor(pedido: any): string {
        if (this.isCancelled(pedido)) return '#e53e3e'; // Red (Cancelado)

        switch (pedido.estado) {
            case 'pendiente_aprobacion': return '#ed8936'; // Orange (Revisión)
            case 'entregado': return '#2f855a'; // Dark Green (Finalizado)

            // All "Aprobado" states (Green/Blue/Purple spectrum but user asked for "Aprobado")
            // We can keep distinct colors or unify them. A unified "Good" color might be better for "Aprobado".
            // Let's keep them somewhat distinct to give more info via color, or unify if "Aprobado" is the only text.
            // If the text is "Aprobado", maybe just Green is fine.
            case 'confirmado':
            case 'pagado':
            case 'en_preparacion':
            case 'enviado':
                return '#48bb78'; // Green

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
