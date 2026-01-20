import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router, RouterModule } from '@angular/router';
import { AuthService } from '../../../services/auth.service';

@Component({
    selector: 'app-reset-password',
    standalone: true,
    imports: [CommonModule, FormsModule, RouterModule],
    templateUrl: './reset-password.component.html',
    styleUrls: ['../request-reset/request-reset.component.css'] // Reuse styles
})
export class ResetPasswordComponent implements OnInit {
    token: string = '';
    password: string = '';
    confirmPassword: string = '';
    loading: boolean = false;
    message: string | null = null;
    error: string | null = null;
    success: boolean = false;

    constructor(
        private route: ActivatedRoute,
        private authService: AuthService,
        private router: Router
    ) { }

    ngOnInit() {
        this.token = this.route.snapshot.queryParamMap.get('token') || '';
        if (!this.token) {
            this.error = 'Token inválido o faltante. Por favor solicita un nuevo enlace.';
        }
    }

    onSubmit() {
        if (!this.token) {
            this.error = 'Token inválido.';
            return;
        }

        if (this.password.length < 8) {
            this.error = 'La contraseña debe tener al menos 8 caracteres.';
            return;
        }

        if (this.password !== this.confirmPassword) {
            this.error = 'Las contraseñas no coinciden.';
            return;
        }

        this.loading = true;
        this.error = null;
        this.message = null;

        this.authService.resetPassword(this.token, this.password).subscribe({
            next: (response) => {
                this.loading = false;
                this.success = true;
                this.message = 'Contraseña actualizada correctamente. Redirigiendo al login...';
                setTimeout(() => {
                    this.router.navigate(['/login']);
                }, 3000);
            },
            error: (err) => {
                this.loading = false;
                this.error = 'El enlace ha expirado o es inválido. Por favor solicita uno nuevo.';
            }
        });
    }
}
