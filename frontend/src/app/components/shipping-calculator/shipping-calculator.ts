import { Component, Input, ChangeDetectorRef } from '@angular/core';
import { CommonModule, Location } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../services/api.service';
import { PickupPointsModalComponent, PuntoRetiro } from '../pickup-points-modal/pickup-points-modal';

@Component({
    selector: 'app-shipping-calculator',
    standalone: true,
    imports: [CommonModule, FormsModule, PickupPointsModalComponent],
    templateUrl: './shipping-calculator.html',
    styleUrl: './shipping-calculator.css'
})
export class ShippingCalculatorComponent {
    @Input() precioBase: number = 0;

    codigoPostal: string = '';
    codigoPostalCalculado: string = ''; // CP actualmente calculado
    calculando: boolean = false;
    opcionesEnvio: any[] = [];
    error: string = '';
    mostrarResultados: boolean = false;
    mostrarTodasOpciones: boolean = false; // Para toggle "Ver más/menos"
    editandoCodigoPostal: boolean = false; // Para mostrar/ocultar campo de cambio

    // Modal de puntos de retiro
    mostrarModalPuntos: boolean = false;
    puntosRetiro: PuntoRetiro[] = [];
    carrierSeleccionado: string = '';

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

        // Llamar a la API una sola vez para obtener todo
        this.apiService.calcularEnvio({
            codigo_postal: this.codigoPostal,
            provincia: 'Buenos Aires'
        }).subscribe({
            next: (res) => {
                const options = Array.isArray(res) ? res : [res];

                this.opcionesEnvio = options.map(opt => ({
                    id: opt.id,
                    nombre: opt.nombre,
                    costo: opt.costo,
                    tiempo: opt.tiempo_estimado || opt.tiempo || '3-5 días hábiles'
                }));

                // Asegurar que "Retiro en Local" esté presente si no vino de la API
                if (!this.opcionesEnvio.find(o => o.id.includes('retiro'))) {
                    this.opcionesEnvio.push({
                        id: 'retiro_local',
                        nombre: 'Retiro en local',
                        costo: 0,
                        tiempo: 'Inmediato'
                    });
                }

                this.calculando = false;
                this.mostrarResultados = true;
                this.codigoPostalCalculado = this.codigoPostal;
                this.editandoCodigoPostal = false;
            },
            error: (err) => {
                console.error('Error calculando envío:', err);
                this.error = 'Hubo un error al calcular los envíos. Por favor intenta más tarde.';
                this.calculando = false;
            }
        });
    }

    private checkFinalizacion(current: number, total: number) {
        if (current === total) {
            this.calculando = false;
            this.mostrarResultados = true;
            this.codigoPostalCalculado = this.codigoPostal;
            this.editandoCodigoPostal = false;
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
        // Ejemplo: 15% de descuento por transferencia sobre el total
        const total = this.precioBase + costoEnvio;
        return total * 0.85;
    }

    cambiarCodigoPostal() {
        this.editandoCodigoPostal = true;
        this.codigoPostalCalculado = '';
        this.mostrarResultados = false;
        this.codigoPostal = '';
    }

    toggleOpciones() {
        this.mostrarTodasOpciones = !this.mostrarTodasOpciones;
    }

    getOpcionesDomicilio() {
        return this.opcionesEnvio.filter(o =>
            o.nombre.toLowerCase().includes('domicilio') ||
            o.nombre.toLowerCase().includes('estándar') ||
            o.nombre.toLowerCase().includes('envío') ||
            o.nombre.toLowerCase().includes('nube') ||
            (o.nombre.toLowerCase().includes('correo') && !o.nombre.toLowerCase().includes('retiro')) ||
            (o.nombre.toLowerCase().includes('andreani') && !o.nombre.toLowerCase().includes('retiro'))
        );
    }

    getOpcionesRetiro() {
        return this.opcionesEnvio.filter(o =>
            o.nombre.toLowerCase().includes('retiro') ||
            o.nombre.toLowerCase().includes('sucursal') ||
            o.id === 'retiro'
        );
    }

    verPuntosRetiro(carrier: string) {
        this.carrierSeleccionado = carrier;
        // Fetch pickup points from API
        this.apiService.getPuntosRetiro(carrier, this.codigoPostalCalculado).subscribe({
            next: (puntos: PuntoRetiro[]) => {
                this.puntosRetiro = puntos;
                this.mostrarModalPuntos = true;
            },
            error: (err: any) => {
                console.error('Error fetching pickup points:', err);
                // Show modal anyway with empty list
                this.puntosRetiro = [];
                this.mostrarModalPuntos = true;
            }
        });
    }

    cerrarModalPuntos() {
        this.mostrarModalPuntos = false;
    }

    seleccionarPunto(punto: PuntoRetiro) {
        console.log('Punto seleccionado:', punto);
        // Aquí puedes almacenar el punto seleccionado
    }
}
