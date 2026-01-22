import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterModule } from '@angular/router';
import { ApiService } from '../../services/api.service';

@Component({
  selector: 'app-encargo-especial',
  imports: [CommonModule, FormsModule, RouterModule],
  templateUrl: './encargo-especial.html',
  styleUrl: './encargo-especial.css'
})
export class EncargoEspecialComponent implements OnInit {
  categorias: any[] = [];
  talles: any[] = [];

  encargo = {
    categoria_id: null as number | null,
    club: '',
    numero: null as number | null,
    dorsal: '',
    talle: null as number | null,
    color: '',
    observaciones: '',
    nombre_cliente: '',
    email_cliente: '',
    telefono_cliente: ''
  };

  enviando = false;
  mensajeExito = false;
  mensajeError = '';

  constructor(private apiService: ApiService) { }

  ngOnInit() {
    this.loadCategorias();
    this.loadTalles();
  }

  loadCategorias() {
    // Pedir lista plana para facilitar la selección directa
    this.apiService.getCategorias(true).subscribe({
      next: (data) => {
        this.categorias = data.sort((a: any, b: any) => a.nombre.localeCompare(b.nombre));
        console.log('Categorías cargadas:', this.categorias);
      },
      error: (error) => {
        console.error('Error cargando categorías:', error);
      }
    });
  }

  loadTalles() {
    this.apiService.getTalles().subscribe({
      next: (data) => {
        this.talles = data;
      },
      error: (error) => {
        console.error('Error cargando talles:', error);
      }
    });
  }

  // Validar email
  validarEmail(email: string): boolean {
    const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return regex.test(email);
  }

  // Validar teléfono argentino
  validarTelefonoArgentino(telefono: string): boolean {
    const telefonoLimpio = telefono.replace(/[\s-]/g, '');
    const regex = /^\+?549?\d{8,12}$/;
    return regex.test(telefonoLimpio);
  }

  enviarEncargo() {
    // Validaciones
    if (!this.encargo.nombre_cliente || !this.encargo.email_cliente || !this.encargo.telefono_cliente) {
      this.mensajeError = 'Por favor completa tus datos de contacto';
      return;
    }

    if (!this.validarEmail(this.encargo.email_cliente)) {
      this.mensajeError = 'Por favor ingresa un email válido (ejemplo@dominio.com)';
      return;
    }

    if (!this.validarTelefonoArgentino(this.encargo.telefono_cliente)) {
      this.mensajeError = 'Por favor ingresa un teléfono argentino válido (+54 9 ...)';
      return;
    }

    if (!this.encargo.categoria_id || !this.encargo.club || !this.encargo.talle) {
      this.mensajeError = 'Por favor selecciona categoría, indica el club/país y selecciona un talle';
      return;
    }

    this.enviando = true;
    this.mensajeError = '';

    const categoria = this.categorias.find(c => c.id === this.encargo.categoria_id);
    const categoriaNombre = categoria?.nombre || 'No especificada';

    // Enviar por WhatsApp
    const mensaje = `🎯 ENCARGO ESPECIAL\n\n` +
      `Categoría: ${categoriaNombre}\n` +
      `Club/País: ${this.encargo.club}\n` +
      `Número: ${this.encargo.numero || 'No especificado'}\n` +
      `Dorsal: ${this.encargo.dorsal || 'No especificado'}\n` +
      `Talle: ${this.talles.find(t => t.id === this.encargo.talle)?.nombre || 'No especificado'}\n` +
      `Color: ${this.encargo.color || 'No especificado'}\n` +
      `Observaciones: ${this.encargo.observaciones || 'Ninguna'}\n\n` +
      `👤 DATOS DEL CLIENTE\n` +
      `Nombre: ${this.encargo.nombre_cliente}\n` +
      `Email: ${this.encargo.email_cliente}\n` +
      `Teléfono: ${this.encargo.telefono_cliente}`;

    const whatsappUrl = `https://wa.me/5493585164402?text=${encodeURIComponent(mensaje)}`;
    window.open(whatsappUrl, '_blank');

    setTimeout(() => {
      this.enviando = false;
      this.mensajeExito = true;
      setTimeout(() => {
        this.mensajeExito = false;
        this.resetForm();
      }, 3000);
    }, 1000);
  }

  resetForm() {
    this.encargo = {
      categoria_id: null,
      club: '',
      numero: null,
      dorsal: '',
      talle: null,
      color: '',
      observaciones: '',
      nombre_cliente: '',
      email_cliente: '',
      telefono_cliente: ''
    };
  }
}
