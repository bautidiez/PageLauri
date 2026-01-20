import { Component } from '@angular/core';
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

  enviado = false;
  enviando = false;
  error = '';

  constructor(private apiService: ApiService) { }

  enviarMensaje() {
    if (this.enviando) return;

    this.enviando = true;
    this.error = '';

    this.apiService.enviarContacto(this.contacto).subscribe({
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
