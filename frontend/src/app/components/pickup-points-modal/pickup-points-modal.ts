import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';

export interface PuntoRetiro {
    nombre: string;
    direccion: string;
    localidad: string;
    provincia: string;
    codigoPostal: string;
}

@Component({
    selector: 'app-pickup-points-modal',
    standalone: true,
    imports: [CommonModule],
    templateUrl: './pickup-points-modal.html',
    styleUrl: './pickup-points-modal.css'
})
export class PickupPointsModalComponent {
    @Input() visible: boolean = false;
    @Input() puntos: PuntoRetiro[] = [];
    @Input() codigoPostal: string = '';
    @Input() carrier: string = ''; // 'correo_argentino' | 'andreani'
    @Output() close = new EventEmitter<void>();
    @Output() selectPoint = new EventEmitter<PuntoRetiro>();

    cerrar() {
        this.close.emit();
    }

    seleccionar(punto: PuntoRetiro) {
        this.selectPoint.emit(punto);
        this.cerrar();
    }

    stopPropagation(event: Event) {
        event.stopPropagation();
    }
}
