import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, RouterModule } from '@angular/router';
import { AuthService } from '../../../services/auth.service';

@Component({
    selector: 'app-request-reset',
    standalone: true,
    imports: [CommonModule, FormsModule, RouterModule],
    templateUrl: './request-reset.component.html',
    styleUrls: ['./request-reset.component.css']
})
export class RequestResetComponent {
    email: string = '';
    loading: boolean = false;
    message: string | null = null;
    error: string | null = null;

    constructor(
        private authService: AuthService,
        private router: Router
    ) { }

    onSubmit() {
        if (!this.email) {
            this.error = 'Por favor ingresa tu email.';
            return;
        }

        this.loading = true;
        this.error = null;
        this.message = null;

        this.authService.requestPasswordReset(this.email).subscribe({
            next: (response) => {
                this.loading = false;
                this.message = 'Si el email existe en nuestro sistema, recibirás un enlace para restablecer tu contraseña.';
                this.email = ''; // Clear input
            },
            error: (err) => {
                this.loading = false;
                // Even on error (e.g. 404), for security we might want to show a generic message or specific one if user-friendly
                if (err.status === 404) {
                    this.error = 'El email no se encuentra registrado.';
                } else {
                    this.error = 'Ocurrió un error. Por favor intenta nuevamente.';
                }
            }
        });
    }
}
