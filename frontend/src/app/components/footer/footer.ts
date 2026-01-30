import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../services/api.service';
import { ToastService } from '../../services/toast.service';

@Component({
  selector: 'app-footer',
  standalone: true,
  imports: [CommonModule, RouterModule, FormsModule],
  templateUrl: './footer.html',
  styleUrl: './footer.css'
})
export class FooterComponent {
  email: string = '';
  nombre: string = '';
  isLoading: boolean = false;

  constructor(
    private apiService: ApiService,
    private toastService: ToastService
  ) { }

  subscribe() {
    if (!this.email) {
      this.toastService.show('Por favor ingresá tu email', 'error');
      return;
    }

    // Validación simple de email
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(this.email)) {
      this.toastService.show('Por favor ingresá un email válido', 'error');
      return;
    }

    this.isLoading = true;
    this.apiService.subscribeNewsletter({
      email: this.email,
      nombre: this.nombre
    }).subscribe({
      next: (res) => {
        this.isLoading = false;
        this.toastService.show(res.message, 'success');
        this.email = '';
        this.nombre = '';
      },
      error: (err) => {
        this.isLoading = false;
        console.error('Error suscribiendo:', err);
        const errorMsg = err.error?.error || 'Ocurrió un error al suscribirte. Intentá nuevamente.';
        this.toastService.show(errorMsg, 'error');
      }
    });
  }
}
