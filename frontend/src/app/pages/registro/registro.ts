import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../services/api.service';
import { Router, ActivatedRoute } from '@angular/router';

@Component({
    selector: 'app-registro',
    standalone: true,
    imports: [CommonModule, FormsModule],
    templateUrl: './registro.html',
    styleUrl: './registro.css'
})
export class RegistroComponent {
    cliente = {
        nombre: '',
        email: '',
        password: '',
        telefono: '',
        acepta_newsletter: true
    };

    registrando = false;
    mensajeExito = false;
    mensajeError = '';
    esperandoVerificacion = false;
    codigoVerificacion = '';
    verificando = false;

    constructor(
        private apiService: ApiService,
        private router: Router,
        private route: ActivatedRoute
    ) {
        this.route.queryParams.subscribe(params => {
            if (params['email'] && params['verify']) {
                this.cliente.email = params['email'];
                this.esperandoVerificacion = true;
            }
        });
    }

    // Validar email
    validarEmail(email: string): boolean {
        const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return regex.test(email);
    }

    // Validar teléfono (más flexible)
    validarTelefono(telefono: string): boolean {
        const telefonoLimpio = telefono.replace(/[\s-().]/g, '');
        // Al menos 8 dígitos, permite prefijos internacionales opcionales
        return telefonoLimpio.length >= 8 && /^\+?\d+$/.test(telefonoLimpio);
    }

    // Validar contraseña compleja
    validarPassword(password: string): boolean {
        // Al menos 8 caracteres, una mayúscula, una minúscula y un número
        const regex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$/;
        return regex.test(password);
    }

    registrar() {
        // ... (validations stay the same)
        if (!this.cliente.nombre || !this.cliente.email || !this.cliente.password || !this.cliente.telefono) {
            this.mensajeError = 'Por favor completa todos los campos';
            return;
        }

        if (!this.validarEmail(this.cliente.email)) {
            this.mensajeError = 'Por favor ingresa un email válido';
            return;
        }

        if (!this.validarTelefono(this.cliente.telefono)) {
            this.mensajeError = 'Por favor ingresa un teléfono válido';
            return;
        }

        if (!this.validarPassword(this.cliente.password)) {
            this.mensajeError = 'La contraseña debe tener al menos 8 caracteres, incluir una mayúscula, una minúscula y un número';
            return;
        }

        this.registrando = true;
        this.mensajeError = '';

        this.apiService.registrarCliente(this.cliente).subscribe({
            next: () => {
                this.esperandoVerificacion = true;
                this.registrando = false;
            },
            error: (error: any) => {
                this.mensajeError = error.error?.error || 'Error al registrar. Intenta nuevamente.';
                this.registrando = false;
            }
        });
    }

    verificarCodigo() {
        if (!this.codigoVerificacion || this.codigoVerificacion.length !== 6) {
            this.mensajeError = 'El código debe ser de 6 dígitos';
            return;
        }

        this.verificando = true;
        this.mensajeError = '';

        this.apiService.verificarCodigo(this.cliente.email, this.codigoVerificacion).subscribe({
            next: () => {
                this.mensajeExito = true;
                this.verificando = false;
                setTimeout(() => {
                    this.router.navigate(['/login']);
                }, 3000);
            },
            error: (error) => {
                this.mensajeError = error.error?.error || 'Código incorrecto';
                this.verificando = false;
            }
        });
    }

    reenviarCodigo() {
        this.apiService.reenviarCodigo(this.cliente.email).subscribe({
            next: () => {
                alert('Código reenviado. Revisa tu WhatsApp o SMS.');
            }
        });
    }
}
