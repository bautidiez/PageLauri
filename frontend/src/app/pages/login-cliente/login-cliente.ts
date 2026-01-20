import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterModule, Router } from '@angular/router';
import { AuthService } from '../../services/auth.service';

@Component({
    selector: 'app-login-cliente',
    standalone: true,
    imports: [CommonModule, FormsModule, RouterModule],
    templateUrl: './login-cliente.html',
    styleUrl: './login-cliente.css',
})
export class LoginClienteComponent {
    email = '';
    password = '';
    error = '';
    loading = false;

    constructor(
        private authService: AuthService,
        private router: Router
    ) { }

    login() {
        if (!this.email || !this.password) {
            this.error = 'Por favor completa todos los campos';
            return;
        }

        this.loading = true;
        this.error = '';

        // Intentar primero como cliente (el campo se llama 'email' pero puede ser el 'username' del admin)
        this.authService.loginCliente(this.email, this.password).subscribe({
            next: () => {
                this.router.navigate(['/']);
            },
            error: (clientError) => {
                // Si el error es falta de verificación, manejamos eso específicamente
                if (clientError.status === 403 && clientError.error?.requires_verification) {
                    alert('Debes verificar tu teléfono antes de entrar. Te redirigimos.');
                    // Podemos guardar el email en un service o pasar por queryParams para el componente de registro
                    this.router.navigate(['/registro'], { queryParams: { email: this.email, verify: true } });
                    return;
                }

                // Si falla como cliente, probamos como administrador
                this.authService.login(this.email, this.password).subscribe({
                    next: () => {
                        this.router.navigate(['/admin']);
                    },
                    error: (adminError) => {
                        // Si ambos fallan, mostramos el error
                        this.error = 'Credenciales incorrectas';
                        this.loading = false;
                    }
                });
            }
        });
    }
}
