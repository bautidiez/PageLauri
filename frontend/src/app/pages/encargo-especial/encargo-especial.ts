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
  categoriasPadre: any[] = [];
  subcategoriasNivel1: any[] = [];
  subcategoriasNivel2: any[] = [];
  talles: any[] = [];

  categoriaPrincipalId: number | null = null;
  subcategoriaNivel1Id: number | null = null;

  encargo = {
    tipo_producto: null as string | null,
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
    this.apiService.getCategorias().subscribe({
      next: (data) => {
        this.categorias = data;
        // Categorías principales (Remeras, Shorts)
        const categoriasPrincipales = data.filter((cat: any) => !cat.categoria_padre_id && cat.activa);
        console.log('Categorías cargadas:', this.categorias);
        console.log('Categorías principales:', categoriasPrincipales);
        // Cargar subcategorías basadas en el tipo de producto si ya está seleccionado
        this.onTipoProductoChange();
      },
      error: (error) => {
        console.error('Error cargando categorías:', error);
      }
    });
  }

  onTipoProductoChange() {
    // Limpiar selecciones previas
    this.categoriaPrincipalId = null;
    this.subcategoriaNivel1Id = null;
    this.encargo.categoria_id = null;
    this.categoriasPadre = [];
    this.subcategoriasNivel1 = [];
    this.subcategoriasNivel2 = [];

    if (!this.encargo.tipo_producto || this.categorias.length === 0) {
      return;
    }

    // Encontrar la categoría principal según el tipo de producto
    const tipoMap: any = {
      'remera': 'Remeras',
      'short': 'Shorts'
    };

    const nombreCategoriaPrincipal = tipoMap[this.encargo.tipo_producto];
    const categoriaPrincipal = this.categorias.find(
      (cat: any) => cat.nombre === nombreCategoriaPrincipal && !cat.categoria_padre_id && cat.activa
    );

    if (categoriaPrincipal) {
      // Cargar las subcategorías de esa categoría principal
      this.categoriasPadre = this.categorias.filter(
        (cat: any) => cat.categoria_padre_id === categoriaPrincipal.id && cat.activa
      );
      console.log(`Subcategorías de ${nombreCategoriaPrincipal}:`, this.categoriasPadre);
    } else {
      console.error(`No se encontró la categoría principal: ${nombreCategoriaPrincipal}`);
    }
  }

  onCategoriaPadreChange(categoriaId: number) {
    this.categoriaPrincipalId = categoriaId;
    this.subcategoriaNivel1Id = null;
    this.encargo.categoria_id = null;

    // Cargar subcategorías nivel 1
    this.subcategoriasNivel1 = this.categorias.filter(
      (cat: any) => cat.categoria_padre_id === categoriaId
    );
    this.subcategoriasNivel2 = [];
  }

  onSubcategoriaNivel1Change(subcategoriaId: number) {
    this.subcategoriaNivel1Id = subcategoriaId;
    this.encargo.categoria_id = subcategoriaId;

    // Cargar subcategorías nivel 2 (ligas)
    this.subcategoriasNivel2 = this.categorias.filter(
      (cat: any) => cat.categoria_padre_id === subcategoriaId
    );
  }

  onSubcategoriaNivel2Change(subcategoriaId: number) {
    this.encargo.categoria_id = subcategoriaId;
  }

  // Verificar si la categoría selected corresponde a países
  get esCategoriaPais(): boolean {
    const categoriasRelacionadasPaises = ['Mundial 2026', 'Selección 24/25', 'Selecciones'];
    const categoriaSeleccionada = this.categorias.find(c => c.id === this.subcategoriaNivel1Id);
    return categoriaSeleccionada && categoriasRelacionadasPaises.includes(categoriaSeleccionada.nombre);
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
    // Acepta formatos: +54 9 11 1234-5678, +54 9 358 123456, etc.
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

    if (!this.encargo.categoria_id || !this.encargo.talle) {
      this.mensajeError = 'Por favor selecciona categoría y talle';
      return;
    }

    this.enviando = true;
    this.mensajeError = '';

    const categoriaNombre = this.categorias.find(c => c.id === this.encargo.categoria_id)?.nombre || 'No especificada';

    // Enviar por WhatsApp
    const mensaje = `🎯 ENCARGO ESPECIAL\n\n` +
      `Tipo: ${this.encargo.tipo_producto === 'remera' ? 'Remera' : 'Short'}\n` +
      `Categoría: ${categoriaNombre}\n` +
      `${this.esCategoriaPais ? 'País' : 'Club'}: ${this.encargo.club || 'No especificado'}\n` +
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
      tipo_producto: null,
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
    this.categoriaPrincipalId = null;
    this.subcategoriaNivel1Id = null;
    this.subcategoriasNivel1 = [];
    this.subcategoriasNivel2 = [];
  }
}
