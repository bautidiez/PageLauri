import { Component, ChangeDetectorRef, NgZone } from '@angular/core';
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
        private router: Router,
        private cdr: ChangeDetectorRef,
        private zone: NgZone
    ) { }

    login() {
        console.log('DEBUG LOGIN: Iniciando proceso para', this.email);
        if (!this.email || !this.password) {
            this.error = 'Por favor completa todos los campos';
            return;
        }

        this.loading = true;
        this.error = '';

        this.authService.loginUnified(this.email, this.password).subscribe({
            next: (response) => {
                console.log('DEBUG LOGIN: Respuesta exitosa', response);
                this.loading = false;
                if (response.user_type === 'admin') {
                    this.router.navigate(['/admin']);
                } else {
                    this.router.navigate(['/']);
                }
            },
            error: (err) => {
                console.error('DEBUG LOGIN: Error en login', err);
                this.zone.run(() => {
                    this.loading = false;
                    if (err.status === 403 && err.error?.requires_verification) {
                        alert('Debes verificar tu email antes de entrar. Te redirigimos.');
                        this.router.navigate(['/registro'], { queryParams: { email: this.email, verify: true } });
                        return;
                    }
                    this.error = 'Credenciales incorrectas o error en servidor';
                    this.cdr.detectChanges();
                });
            }
        });
    }
}
