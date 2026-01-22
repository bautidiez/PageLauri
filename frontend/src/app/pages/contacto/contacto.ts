import { Component, HostListener } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../services/api.service';

@Component({
  selector: 'app-contacto',
  imports: [CommonModule, FormsModule],
  templateUrl: './contacto.html',
  styleUrl: './contacto.css'
})
export class ContactoComponent {
  contacto = {
    nombre: '',
    email: '',
    telefono: '',
    mensaje: ''
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

  enviado = false;
  enviando = false;
  error = '';

  constructor(private apiService: ApiService) { }

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

  enviarMensaje() {
    if (this.enviando) return;

    this.enviando = true;
    this.error = '';

    // Combinar prefijo con teléfono para el envío
    const contactoParaEnviar = {
      ...this.contacto,
      telefono: `${this.prefijoTelefono} ${this.contacto.telefono}`
    };

    this.apiService.enviarContacto(contactoParaEnviar).subscribe({
      next: (response) => {
        console.log('Mensaje enviado exitosamente:', response);
        this.enviado = true;
        this.enviando = false;

        // Limpiar el formulario después de 5 segundos
        setTimeout(() => {
          this.enviado = false;
          this.contacto = { nombre: '', email: '', telefono: '', mensaje: '' };
        }, 5000);
      },
      error: (err) => {
        console.error('Error al enviar mensaje:', err);
        this.enviando = false;
        this.error = err.error?.error || 'Error al enviar el mensaje. Por favor, intenta nuevamente.';

        // Limpiar el error después de 5 segundos
        setTimeout(() => {
          this.error = '';
        }, 5000);
      }
    });
  }
}
