import { Component, Input, ChangeDetectorRef } from '@angular/core';
import { CommonModule, Location } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../services/api.service';

@Component({
    selector: 'app-shipping-calculator',
    standalone: true,
    imports: [CommonModule, FormsModule],
    templateUrl: './shipping-calculator.html',
    styleUrl: './shipping-calculator.css'
})
export class ShippingCalculatorComponent {
    @Input() precioBase: number = 0;

    codigoPostal: string = '';
    calculando: boolean = false;
    opcionesEnvio: any[] = [];
    error: string = '';
    mostrarResultados: boolean = false;

    constructor(
        private apiService: ApiService,
        private location: Location,
        private cdr: ChangeDetectorRef
    ) {
        // Recuperar CP de localStorage si existe
        const savedCP = localStorage.getItem('codigo_postal');
        if (savedCP) {
            this.codigoPostal = savedCP;
        }
    }

    volver(): void {
        this.location.back();
    }

    calcular() {
        if (!this.codigoPostal || this.codigoPostal.length < 4) {
            this.error = 'Por favor ingresa un código postal válido';
            return;
        }

        this.calculando = true;
        this.error = '';
        this.opcionesEnvio = [];

        // Guardar CP
        localStorage.setItem('codigo_postal', this.codigoPostal);

        const metodos = ['correo_argentino', 'andreani', 'tienda_nube', 'retiro'];
        let completed = 0;

        metodos.forEach(metodo => {
            if (metodo === 'retiro') {
                this.opcionesEnvio.push({
                    id: 'retiro',
                    nombre: 'Retiro en local',
                    costo: 0,
                    tiempo: 'Inmediato'
                });
                completed++;
                this.checkFinalizacion(completed, metodos.length);
                return;
            }

            this.apiService.calcularEnvio({
                codigo_postal: this.codigoPostal,
                metodo_envio: metodo,
                provincia: 'Buenos Aires' // Default o inferido
            }).subscribe({
                next: (res) => {
                    const arrayRes = Array.isArray(res) ? res : [res];
                    arrayRes.forEach(opt => {
                        this.opcionesEnvio.push({
                            id: opt.id || metodo,
                            nombre: opt.nombre || this.getNombreMetodo(metodo),
                            costo: opt.costo || 0,
                            tiempo: opt.tiempo_estimado || opt.tiempo || '3-5 días hábiles'
                        });
                    });
                    completed++;
                    this.checkFinalizacion(completed, metodos.length);
                },
                error: () => {
                    completed++;
                    this.checkFinalizacion(completed, metodos.length);
                }
            });
        });
    }

    private checkFinalizacion(current: number, total: number) {
        if (current === total) {
            this.calculando = false;
            this.mostrarResultados = true;
            // Ordenar por costo
            this.opcionesEnvio.sort((a, b) => a.costo - b.costo);
            // Forzar detección de cambios para mostrar resultados inmediatamente
            this.cdr.detectChanges();
        }
    }

    private getNombreMetodo(id: string): string {
        const nombres: any = {
            'correo_argentino': 'Correo Argentino',
            'andreani': 'Andreani',
            'tienda_nube': 'Tienda Nube'
        };
        return nombres[id] || id;
    }

    getPrecioConTransferencia(costoEnvio: number): number {
        // Ejemplo: 10% de descuento por transferencia sobre el total
        const total = this.precioBase + costoEnvio;
        return total * 0.9;
    }
}
