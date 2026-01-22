import { Component, ChangeDetectorRef, NgZone, HostListener, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../services/api.service';
import { Router, ActivatedRoute, RouterLink } from '@angular/router';

@Component({
    selector: 'app-registro',
    standalone: true,
    imports: [CommonModule, FormsModule, RouterLink],
    templateUrl: './registro.html',
    styleUrl: './registro.css'
})
export class RegistroComponent implements OnInit {
    cliente = {
        nombre: '',
        email: '',
        password: '',
        telefono: '',
        metodo_verificacion: 'telefono', // 'email' o 'telefono'
        acepta_newsletter: true
    };

    prefijos = [
        { nombre: 'Argentina', codigo: '+54 9', flag: '🇦🇷', iso: 'ar' },
        { nombre: 'Uruguay', codigo: '+598', flag: '🇺🇾', iso: 'uy' },
        { nombre: 'Chile', codigo: '+56', flag: '🇨🇱', iso: 'cl' },
        { nombre: 'Paraguay', codigo: '+595', flag: '🇵🇾', iso: 'py' },
        { nombre: 'Bolivia', codigo: '+591', flag: '🇧🇴', iso: 'bo' },
        { nombre: 'Brasil', codigo: '+55', flag: '🇧🇷', iso: 'br' },
        { nombre: 'Perú', codigo: '+51', flag: '🇵🇪', iso: 'pe' },
        { nombre: 'Ecuador', codigo: '+593', flag: '🇪🇨', iso: 'ec' },
        { nombre: 'Colombia', codigo: '+57', flag: '🇨🇴', iso: 'co' },
        { nombre: 'Venezuela', codigo: '+58', flag: '🇻🇪', iso: 've' },
        { nombre: 'México', codigo: '+52', flag: '🇲🇽', iso: 'mx' },
        { nombre: 'España', codigo: '+34', flag: '🇪🇸', iso: 'es' },
        { nombre: 'USA', codigo: '+1', flag: '🇺🇸', iso: 'us' }
    ];

    prefijoTelefono = '+54 9';
    dropdownAbierto = false;

    registrando = false;
    mensajeExito = false;
    mensajeError = '';
    esperandoVerificacion = false;
    codigoVerificacion = '';
    verificando = false;

    constructor(
        private apiService: ApiService,
        private router: Router,
        private route: ActivatedRoute,
        private cdr: ChangeDetectorRef,
        private zone: NgZone
    ) {
        this.route.queryParams.subscribe(params => {
            if (params['email'] && params['verify']) {
                this.cliente.email = params['email'];
                this.esperandoVerificacion = true;
            }
        });
    }

    ngOnInit() {
        // Restaurar estado si existe en localStorage (para recargas accidentales en móvil)
        const savedState = localStorage.getItem('pending_registration');
        if (savedState) {
            try {
                const data = JSON.parse(savedState);
                if (data.email && data.esperando) {
                    this.cliente.email = data.email;
                    this.cliente.metodo_verificacion = data.metodo || 'telefono';
                    this.esperandoVerificacion = true;
                    console.log('DEBUG REGISTRO: Estado restaurado para', data.email);
                }
            } catch (e) {
                localStorage.removeItem('pending_registration');
            }
        }
    }

    @HostListener('document:click', ['$event'])
    onClickDocument(event: MouseEvent) {
        const target = event.target as HTMLElement;
        if (!target.closest('.custom-prefix-selector')) {
            this.dropdownAbierto = false;
        }
    }

    toggleDropdown() {
        this.dropdownAbierto = !this.dropdownAbierto;
    }

    seleccionarPrefijo(codigo: string) {
        this.prefijoTelefono = codigo;
        this.dropdownAbierto = false;
    }

    getPrefijoActual() {
        return this.prefijos.find(p => p.codigo === this.prefijoTelefono) || this.prefijos[0];
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

        // Combinar prefijo con teléfono para el envío
        const clienteParaEnviar = {
            ...this.cliente,
            telefono: `${this.prefijoTelefono} ${this.cliente.telefono}`
        };

        this.apiService.registrarCliente(clienteParaEnviar).subscribe({
            next: () => {
                this.zone.run(() => {
                    // Guardar estado en localStorage
                    localStorage.setItem('pending_registration', JSON.stringify({
                        email: this.cliente.email,
                        metodo: this.cliente.metodo_verificacion,
                        esperando: true
                    }));

                    this.esperandoVerificacion = true;
                    this.registrando = false;
                    this.cdr.detectChanges();
                });
            },
            error: (error: any) => {
                this.zone.run(() => {
                    this.mensajeError = error.error?.error || 'Error al registrar. Intenta nuevamente.';
                    this.registrando = false;
                    this.cdr.detectChanges();
                });
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

        const codigoLimpio = this.codigoVerificacion.trim();

        this.apiService.verificarCodigo(this.cliente.email, codigoLimpio).subscribe({
            next: () => {
                this.zone.run(() => {
                    localStorage.removeItem('pending_registration');
                    this.mensajeExito = true;
                    this.verificando = false;
                    this.cdr.detectChanges();
                    setTimeout(() => {
                        this.router.navigate(['/login']);
                    }, 3000);
                });
            },
            error: (error) => {
                this.zone.run(() => {
                    this.mensajeError = error.error?.error || 'Código incorrecto';
                    this.verificando = false;
                    this.cdr.detectChanges();
                });
            }
        });
    }

    reenviarCodigo() {
        this.apiService.reenviarCodigo(this.cliente.email).subscribe({
            next: () => {
                const destino = this.cliente.metodo_verificacion === 'email' ? 'email' : 'WhatsApp/SMS';
                alert(`Código reenviado. Revisa tu ${destino}.`);
            }
        });
    }
}
