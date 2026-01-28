import { Component, OnInit, ChangeDetectorRef, NgZone } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterModule, Router } from '@angular/router';
import { ApiService } from '../../../services/api.service';
import { AuthService } from '../../../services/auth.service';
import { ColorPickerComponent } from '../../../components/color-picker/color-picker.component';

@Component({
  selector: 'app-productos-admin',
  imports: [CommonModule, FormsModule, RouterModule, ColorPickerComponent],
  templateUrl: './productos-admin.html',
  styleUrl: './productos-admin.css'
})
export class ProductosAdminComponent implements OnInit {
  productos: any[] = [];
  categorias: any[] = [];
  categoriasPadre: any[] = [];
  subcategoriasNivel1: any[] = [];  // Temporadas/Tipos (Retro, 24/25, etc.)
  subcategoriasNivel2: any[] = [];  // Ligas (Premier, La Liga, etc.)
  categoriaPadreSeleccionada: number | null = null;
  subcategoriaNivel1Seleccionada: number | null = null;
  mostrarSubcategorias = false;  // Solo mostrar subcategorías si es Remeras
  public colorSeleccionado: string = '';
  public productosRelacionados: any[] = [];
  public productoRelacionadoId: number | null = null;

  // Propiedades para la búsqueda de productos relacionados (Autocomplete)
  public busquedaProductoRelacionado: string = '';
  public productosRelacionadosFiltrados: any[] = [];

  loading = true;
  mostrarFormulario = false;
  productoEditando: any = null;

  // Paginado
  paginaActual = 1;
  productosPorPagina = 40;
  totalProductos = 0;
  totalPaginas = 0;

  // Filtros de lista
  filtroCategoria: number | null = null;
  filtroSubcategoria: number | null = null;
  filtroSubsubcategoria: number | null = null;
  filtroEstadoStock: string = '';  // '', 'disponible', 'bajo', 'no_disponible'
  filtroBusqueda = '';

  // Listas para desplegables de filtros en cascada
  subcategoriasDisponibles: any[] = [];
  subsubcategoriasDisponibles: any[] = [];

  nuevoProducto: any = {
    nombre: '',
    descripcion: '',
    precio_base: 0,
    precio_descuento: null,
    categoria_id: null as number | null,
    activo: null as boolean | null,
    destacado: false,
    color: '',
    color_hex: '',
    producto_relacionado_id: null as number | null,
    dorsal: '',
    numero: null,
    version: ''
  };

  imagenesSeleccionadas: File[] = [];
  imagenesPreview: string[] = [];
  imagenesExistentes: any[] = [];

  constructor(
    private apiService: ApiService,
    private authService: AuthService,
    private router: Router,
    private cdr: ChangeDetectorRef,
    private zone: NgZone
  ) { }

  // Expo Math para el template
  Math = Math;

  ngOnInit() {
    if (!this.authService.isLoggedIn()) {
      this.router.navigate(['/admin/login']);
      return;
    }
    this.loadProductos();
    this.loadCategorias();
  }

  loadProductos() {
    // Solo mostrar loading si no hay datos previos
    if (this.productos.length === 0) {
      this.loading = true;
    }

    const filtros: any = {};
    if (this.filtroCategoria) filtros.categoria_id = this.filtroCategoria;
    if (this.filtroSubcategoria) filtros.subcategoria_id = this.filtroSubcategoria;
    if (this.filtroSubsubcategoria) filtros.subsubcategoria_id = this.filtroSubsubcategoria;
    if (this.filtroEstadoStock) filtros.estado_stock = this.filtroEstadoStock;
    if (this.filtroBusqueda) filtros.busqueda = this.filtroBusqueda;

    // Paginado
    filtros.page = this.paginaActual;
    filtros.page_size = this.productosPorPagina;
    filtros.activos = false;  // Mostrar todos en admin

    this.apiService.getProductos(filtros).subscribe({
      next: (data) => {
        // Manejar respuesta paginada o array
        if (data.items) {
          // Respuesta paginada del backend
          this.productos = data.items;
          this.totalProductos = data.total || data.items.length;
          this.totalPaginas = Math.ceil(this.totalProductos / this.productosPorPagina);
        } else {
          // Array simple (fallback)
          this.productos = data;
          this.totalProductos = data.length;
          this.totalPaginas = 1;
        }
        this.loading = false;
        this.cdr.detectChanges();
      },
      error: (error) => {
        console.error('Error cargando productos:', error);
        this.loading = false;
        this.cdr.detectChanges();
      }
    });
  }

  filtrarPorCategoria() {
    this.loadProductos();
  }

  buscarProductos() {
    this.loadProductos();
  }

  limpiarFiltros() {
    this.filtroCategoria = null;
    this.filtroSubcategoria = null;
    this.filtroSubsubcategoria = null;
    this.filtroEstadoStock = '';
    this.filtroBusqueda = '';
    this.subcategoriasDisponibles = [];
    this.subsubcategoriasDisponibles = [];
    this.paginaActual = 1;
    this.loadProductos();
  }

  onFiltroCategoriaChange() {
    // Resetear filtros dependientes
    this.filtroSubcategoria = null;
    this.filtroSubsubcategoria = null;
    this.subsubcategoriasDisponibles = [];

    // Cargar subcategorías disponibles basadas en la categoría seleccionada
    if (this.filtroCategoria) {
      this.subcategoriasDisponibles = this.categorias.filter((cat: any) =>
        cat.categoria_padre_id === this.filtroCategoria
      );
    } else {
      this.subcategoriasDisponibles = [];
    }

    this.loadProductos();
  }

  onFiltroSubcategoriaChange() {
    // Resetear filtro de sub-subcategoría
    this.filtroSubsubcategoria = null;

    // Cargar sub-subcategorías disponibles
    if (this.filtroSubcategoria) {
      this.subsubcategoriasDisponibles = this.categorias.filter((cat: any) =>
        cat.categoria_padre_id === this.filtroSubcategoria
      );
    } else {
      this.subsubcategoriasDisponibles = [];
    }

    this.loadProductos();
  }

  loadCategorias() {
    this.apiService.getCategorias(true, undefined, true).subscribe({
      next: (data) => {
        // Asegurar que todos los IDs sean números y filtrar 'Ofertas'
        this.categorias = data.map((c: any) => ({
          ...c,
          id: Number(c.id),
          categoria_padre_id: c.categoria_padre_id ? Number(c.categoria_padre_id) : null
        })).filter((c: any) => (c.nombre || '').trim().toLowerCase() !== 'ofertas');

        // SOLO Remeras y Shorts como padres principales
        this.categoriasPadre = this.categorias.filter((cat: any) => {
          const nombre = (cat.nombre || '').trim().toLowerCase();
          return !cat.categoria_padre_id && (nombre === 'remeras' || nombre === 'shorts');
        });

        console.log('Categorías padre filtradas:', this.categoriasPadre);
        console.log('Total categorías cargadas (sin ofertas):', this.categorias.length);
        console.log('--- DEBUG CATEGORÍAS ---');
        console.log('Categorías Padre:', this.categoriasPadre.map(c => `${c.nombre}(${c.id})`));
        console.log('Total Categorías:', this.categorias.length);
        const l3_sample = this.categorias.find(c => {
          const padre = this.categorias.find(p => p.id === c.categoria_padre_id);
          return padre && padre.categoria_padre_id !== null;
        });
        console.log('Ejemplo Nivel 3 en memoria:', l3_sample ? `${l3_sample.nombre} -> ${l3_sample.categoria_padre_id}` : 'Ninguna');
        this.cdr.detectChanges();
      },
      error: (error) => {
        console.error('Error cargando categorías:', error);
        this.categoriasPadre = [];
        this.categorias = [];
        this.cdr.detectChanges();
      }
    });
  }

  onColorSelected(colorObj: any) {
    if (colorObj && colorObj.name) {
      this.nuevoProducto.color = colorObj.name;
      this.colorSeleccionado = colorObj.hex;
      this.nuevoProducto.color_hex = colorObj.hex;
    }
  }

  getColorByName(name: string): any {
    const colors = [
      { name: 'Rojo', hex: '#FF0000' },
      { name: 'Azul', hex: '#0000FF' },
      { name: 'Verde', hex: '#00FF00' },
      { name: 'Amarillo', hex: '#FFFF00' },
      { name: 'Naranja', hex: '#FFA500' },
      { name: 'Rosa', hex: '#FFC0CB' },
      { name: 'Morado', hex: '#800080' },
      { name: 'Negro', hex: '#000000' },
      { name: 'Blanco', hex: '#FFFFFF' },
      { name: 'Gris', hex: '#808080' },
      { name: 'Marrón', hex: '#A52A2A' },
      { name: 'Dorado', hex: '#FFD700' },
      { name: 'Plateado', hex: '#C0C0C0' },
      { name: 'Turquesa', hex: '#40E0D0' },
      { name: 'Verde Lima', hex: '#32CD32' },
      { name: 'Azul Marino', hex: '#000080' },
      { name: 'Rojo Oscuro', hex: '#8B0000' },
      { name: 'Verde Oscuro', hex: '#006400' },
      { name: 'Azul Cielo', hex: '#87CEEB' },
      { name: 'Coral', hex: '#FF7F50' }
    ];
    return colors.find(c => c.name === name);
  }

  onCategoriaPadreChange() {
    // Normalizar a número
    const selectedId = this.categoriaPadreSeleccionada ? Number(this.categoriaPadreSeleccionada) : null;
    this.categoriaPadreSeleccionada = selectedId;

    // Resetear selecciones de nivel inferior
    this.subcategoriaNivel1Seleccionada = null;
    this.subcategoriasNivel1 = [];
    this.subcategoriasNivel2 = [];
    this.nuevoProducto.categoria_id = null;

    if (selectedId) {
      this.mostrarSubcategorias = true;

      // Cargar subcategorías de nivel 1 (Temporadas/Tipos)
      this.subcategoriasNivel1 = this.categorias.filter((cat: any) =>
        cat.categoria_padre_id === selectedId
      );

      if (this.subcategoriasNivel1.length === 0) {
        this.nuevoProducto.categoria_id = selectedId;
      }
    } else {
      this.mostrarSubcategorias = false;
    }
  }

  onSubcategoriaNivel1Change() {
    // Normalizar a número
    const selectedId = this.subcategoriaNivel1Seleccionada ? Number(this.subcategoriaNivel1Seleccionada) : null;
    this.subcategoriaNivel1Seleccionada = selectedId;

    this.subcategoriasNivel2 = [];
    this.nuevoProducto.categoria_id = null;

    if (selectedId) {
      // Cargar sub-subcategorías (Ligas)
      this.subcategoriasNivel2 = this.categorias.filter((cat: any) =>
        cat.categoria_padre_id === selectedId
      );

      console.log(`Buscando L3 para PadreID ${selectedId}. Encontrados: ${this.subcategoriasNivel2.length}`);
      if (this.subcategoriasNivel2.length > 0) {
        console.log('Primeras L3:', this.subcategoriasNivel2.slice(0, 2).map(c => c.nombre));
      }

      if (this.subcategoriasNivel2.length === 0) {
        this.nuevoProducto.categoria_id = selectedId;
      }
    }
  }

  nuevo() {
    this.productoEditando = null;
    this.categoriaPadreSeleccionada = null;
    this.subcategoriaNivel1Seleccionada = null;
    this.subcategoriasNivel1 = [];
    this.subcategoriasNivel2 = [];
    this.mostrarSubcategorias = false;
    this.colorSeleccionado = '';
    this.productoRelacionadoId = null;
    this.nuevoProducto = {
      nombre: '',
      descripcion: '',
      precio_base: 0,
      precio_descuento: null,
      categoria_id: null as number | null,
      activo: null as boolean | null,
      destacado: false,
      color: '',
      color_hex: '',
      producto_relacionado_id: null,
      dorsal: '',
      numero: null,
      version: ''
    };
    this.imagenesSeleccionadas = [];
    this.imagenesPreview = [];
    this.imagenesExistentes = [];
    this.mostrarFormulario = true;
  }

  editar(producto: any) {
    this.productoEditando = producto;

    // Encontrar la categoría del producto y toda su jerarquía
    const categoriaProducto = this.categorias.find((c: any) => c.id === producto.categoria_id);

    if (categoriaProducto) {
      // Determinar la jerarquía de categorías
      if (categoriaProducto.categoria_padre_id) {
        // Hay al menos 1 nivel padre
        const categoriaNivel1 = this.categorias.find((c: any) => c.id === categoriaProducto.categoria_padre_id);

        if (categoriaNivel1 && categoriaNivel1.categoria_padre_id) {
          // Hay 3 niveles: Liga -> Temporada -> Remeras
          this.categoriaPadreSeleccionada = categoriaNivel1.categoria_padre_id;
          this.onCategoriaPadreChange();
          this.subcategoriaNivel1Seleccionada = categoriaNivel1.id;
          this.onSubcategoriaNivel1Change();
          this.nuevoProducto.categoria_id = producto.categoria_id;
        } else if (categoriaNivel1) {
          // Hay 2 niveles: Temporada -> Remeras
          this.categoriaPadreSeleccionada = categoriaNivel1.id;
          this.onCategoriaPadreChange();
          this.subcategoriaNivel1Seleccionada = producto.categoria_id;
          this.onSubcategoriaNivel1Change();
        }
      } else {
        // Es una categoría principal (Shorts u Ofertas)
        this.categoriaPadreSeleccionada = producto.categoria_id;
        this.subcategoriasNivel1 = [];
        this.subcategoriasNivel2 = [];
        this.mostrarSubcategorias = false;
        this.nuevoProducto.categoria_id = producto.categoria_id;
      }
    }

    this.colorSeleccionado = producto.color_hex || '';
    this.productoRelacionadoId = producto.producto_relacionado_id || null;
    this.nuevoProducto = {
      nombre: producto.nombre,
      descripcion: producto.descripcion || '',
      precio_base: producto.precio_base,
      precio_descuento: producto.precio_descuento,
      categoria_id: producto.categoria_id,
      activo: producto.activo,
      destacado: producto.destacado,
      color: producto.color || '',
      color_hex: producto.color_hex || '',
      producto_relacionado_id: producto.producto_relacionado_id || null,
      dorsal: producto.dorsal || '',
      numero: producto.numero || null,
      version: producto.version || ''
    };
    this.imagenesSeleccionadas = [];
    this.imagenesPreview = [];
    this.imagenesExistentes = producto.imagenes || [];
    this.mostrarFormulario = true;
  }

  guardar() {
    // Convertir valores string a number
    if (typeof this.categoriaPadreSeleccionada === 'string' && this.categoriaPadreSeleccionada !== '') {
      this.categoriaPadreSeleccionada = parseInt(this.categoriaPadreSeleccionada);
    }
    if (typeof this.nuevoProducto.categoria_id === 'string' && this.nuevoProducto.categoria_id !== '') {
      this.nuevoProducto.categoria_id = parseInt(this.nuevoProducto.categoria_id as unknown as string);
    }

    // Si no hay subcategorías, usar la categoría padre
    if (!this.nuevoProducto.categoria_id && this.categoriaPadreSeleccionada) {
      this.nuevoProducto.categoria_id = this.categoriaPadreSeleccionada as number;
    }

    // Asignar producto relacionado
    if (this.productoRelacionadoId) {
      this.nuevoProducto.producto_relacionado_id = this.productoRelacionadoId;
    }

    if (!this.nuevoProducto.nombre || !this.nuevoProducto.precio_base || this.nuevoProducto.precio_base <= 0 || !this.nuevoProducto.categoria_id) {
      alert('Por favor completa todos los campos requeridos (Nombre, Precio Base y Categoría)');
      return;
    }

    if (this.productoEditando) {
      // Actualizar producto
      this.apiService.updateProducto(this.productoEditando.id, this.nuevoProducto).subscribe({
        next: (productoActualizado) => {
          // Subir imágenes si hay nuevas
          if (this.imagenesSeleccionadas.length > 0) {
            this.subirImagenes(productoActualizado.id);
          } else {
            this.loadProductos();
            this.cancelar();
            alert('Producto actualizado exitosamente');
          }
        },
        error: (error) => {
          const mensaje = error.error?.error || error.message || 'Error al actualizar producto';
          alert('Error al actualizar producto: ' + mensaje);
          console.error('Error completo:', error);
        }
      });
    } else {
      // Crear nuevo producto
      this.apiService.createProducto(this.nuevoProducto).subscribe({
        next: (nuevoProducto) => {
          // Subir imágenes si hay
          if (this.imagenesSeleccionadas.length > 0) {
            this.subirImagenes(nuevoProducto.id);
          } else {
            this.loadProductos();
            this.cancelar();
            alert('Producto creado exitosamente');
          }
        },
        error: (error) => {
          const mensaje = error.error?.error || error.message || 'Error desconocido';
          alert('Error al crear producto: ' + mensaje);
          console.error('Error completo:', error);
        }
      });
    }
  }

  subirImagenes(productoId: number) {
    let imagenesSubidas = 0;
    const totalImagenes = this.imagenesSeleccionadas.length;

    if (totalImagenes === 0) {
      this.loadProductos();
      this.cancelar();
      return;
    }

    this.imagenesSeleccionadas.forEach((file, index) => {
      const esPrincipal = index === 0;
      this.apiService.uploadImagen(productoId, file, esPrincipal, index).subscribe({
        next: () => {
          imagenesSubidas++;
          if (imagenesSubidas === totalImagenes) {
            this.loadProductos();
            this.cancelar();
            alert('Producto ' + (this.productoEditando ? 'actualizado' : 'creado') + ' e imágenes subidas exitosamente');
          }
        },
        error: (error) => {
          console.error('Error subiendo imagen:', error);
          imagenesSubidas++;
          if (imagenesSubidas === totalImagenes) {
            this.loadProductos();
            this.cancelar();
            alert('Producto ' + (this.productoEditando ? 'actualizado' : 'creado') + ' pero hubo errores al subir algunas imágenes');
          }
        }
      });
    });
  }

  onFileSelected(event: any) {
    const files = Array.from(event.target.files) as File[];
    this.imagenesSeleccionadas = [...this.imagenesSeleccionadas, ...files];

    // Crear previews
    files.forEach(file => {
      const reader = new FileReader();
      reader.onload = (e: any) => {
        this.zone.run(() => {
          this.imagenesPreview.push(e.target.result);
          this.cdr.detectChanges();
        });
      };
      reader.readAsDataURL(file);
    });
  }

  eliminarImagenPreview(index: number) {
    this.imagenesPreview.splice(index, 1);
    this.imagenesSeleccionadas.splice(index, 1);
  }

  eliminarImagenExistente(imagenId: number) {
    if (confirm('¿Estás seguro de eliminar esta imagen?')) {
      this.apiService.deleteImagen(imagenId).subscribe({
        next: () => {
          this.imagenesExistentes = this.imagenesExistentes.filter(img => img.id !== imagenId);
          this.loadProductos();
        },
        error: (error) => {
          alert('Error al eliminar imagen');
          console.error(error);
        }
      });
    }
  }

  eliminar(producto: any) {
    if (confirm(`¿Estás seguro de eliminar "${producto.nombre}"?`)) {
      this.apiService.deleteProducto(producto.id).subscribe({
        next: () => {
          this.loadProductos();
          alert(`Producto "${producto.nombre}" eliminado exitosamente`);
        },
        error: (error) => {
          const errorData = error.error;

          // Si el backend sugiere desactivar en lugar de eliminar
          if (errorData && errorData.suggestion === 'desactivar') {
            const mensaje = `${errorData.error}\n\n¿Quieres DESACTIVAR el producto en su lugar?\n\n(El producto dejará de mostrarse en la tienda pero se mantendrá el historial)`;
            const desactivar = confirm(mensaje);

            if (desactivar) {
              // Desactivar el producto
              this.apiService.updateProducto(producto.id, { activo: false }).subscribe({
                next: () => {
                  this.loadProductos();
                  alert(`Producto "${producto.nombre}" desactivado exitosamente`);
                },
                error: (err) => {
                  alert('Error al desactivar producto');
                  console.error(err);
                }
              });
            }
          } else {
            // Mostrar error genérico
            const mensajeError = errorData?.error || error.message || 'Error al eliminar producto';
            alert(mensajeError);
          }

          console.error('Error completo:', error);
        }
      });
    }
  }

  cancelar() {
    this.mostrarFormulario = false;
    this.productoEditando = null;
  }

  getImagenPrincipal(producto: any): string {
    if (producto.imagenes && producto.imagenes.length > 0) {
      const principal = producto.imagenes.find((img: any) => img.es_principal);
      if (principal) return this.apiService.getFormattedImageUrl(principal.url);
      return this.apiService.getFormattedImageUrl(producto.imagenes[0].url);
    }
    return 'https://via.placeholder.com/150x150?text=Sin+imagen';
  }

  getFormattedImageUrl(url: string | null | undefined): string {
    return this.apiService.getFormattedImageUrl(url);
  }

  // --- MÉTODOS PARA PRODUCTO RELACIONADO (AUTOCOMPLETE) ---

  buscarProductoRelacionado() {
    if (!this.busquedaProductoRelacionado || this.busquedaProductoRelacionado.length < 2) {
      this.productosRelacionadosFiltrados = [];
      return;
    }

    const termino = this.busquedaProductoRelacionado.toLowerCase();
    this.productosRelacionadosFiltrados = this.productos.filter(p =>
      p.nombre.toLowerCase().includes(termino) &&
      p.id !== this.nuevoProducto.id &&
      (!this.productoEditando || p.id !== this.productoEditando.id)
    ).slice(0, 10); // Limitar a 10 resultados
  }

  seleccionarProductoRelacionado(producto: any) {
    this.nuevoProducto.producto_relacionado_id = producto.id;
    this.busquedaProductoRelacionado = producto.nombre;
    this.productosRelacionadosFiltrados = [];
  }

  limpiarProductoRelacionado() {
    this.nuevoProducto.producto_relacionado_id = null;
    this.busquedaProductoRelacionado = '';
    this.productosRelacionadosFiltrados = [];
  }

  getCleanCategoryPath(catId: number | null, pathNodes: number[] = []): string {
    if (!catId) return '';

    // Evitar recursión infinita
    if (pathNodes.includes(catId)) {
      return '';
    }

    const cat = this.categorias.find(c => Number(c.id) === Number(catId));
    if (!cat) return '';

    if (!cat.categoria_padre_id) {
      return cat.nombre;
    }

    const padre = this.categorias.find(p => Number(p.id) === Number(cat.categoria_padre_id));
    if (padre && padre.id !== catId) {
      return `${this.getCleanCategoryPath(padre.id, [...pathNodes, catId])} > ${cat.nombre}`;
    }

    return cat.nombre;
  }

  getCategoryPath(catId: number | null): string {
    if (!catId) return '-';

    // Obtenemos el path sin iconos
    const path = this.getCleanCategoryPath(catId);

    // Verificamos si es una categoría principal para poner el icono
    const cat = this.categorias.find(c => c.id === catId);
    if (cat && !cat.categoria_padre_id) {
      return `🏠 ${path}`;
    }

    return path || '-';
  }

  // Métodos de paginado
  cambiarPagina(pagina: number) {
    if (pagina >= 1 && pagina <= this.totalPaginas) {
      this.paginaActual = pagina;
      this.loadProductos();
      window.scrollTo(0, 0);
    }
  }

  siguientePagina() {
    this.cambiarPagina(this.paginaActual + 1);
  }

  anteriorPagina() {
    this.cambiarPagina(this.paginaActual - 1);
  }

  getPaginasArray(): number[] {
    const paginas: number[] = [];
    const maxBotones = 5; // Mostrar máximo 5 botones de página

    let inicio = Math.max(1, this.paginaActual - Math.floor(maxBotones / 2));
    let fin = Math.min(this.totalPaginas, inicio + maxBotones - 1);

    // Ajustar si estamos cerca del final
    if (fin - inicio < maxBotones - 1) {
      inicio = Math.max(1, fin - maxBotones + 1);
    }

    for (let i = inicio; i <= fin; i++) {
      paginas.push(i);
    }

    return paginas;
  }

  formatPrecio(precio: number): string {
    if (!precio) return '0';
    // Formato manual para asegurar punto como separador de miles
    return precio.toString().replace(/\B(?=(\d{3})+(?!\d))/g, '.');
  }
}

