import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterModule, Router } from '@angular/router';
import { ApiService } from '../../../services/api.service';
import { AuthService } from '../../../services/auth.service';

interface Categoria {
    id?: number;
    nombre: string;
    descripcion: string;
    imagen?: string;
    orden: number;
    categoria_padre_id?: number | null;
    activa: boolean;
    nivel?: number;
    subcategorias?: Categoria[];
}

@Component({
    selector: 'app-categorias-admin',
    imports: [CommonModule, FormsModule, RouterModule],
    templateUrl: './categorias-admin.html',
    styleUrl: './categorias-admin.css'
})
export class CategoriasAdminComponent implements OnInit {
    categorias: Categoria[] = [];
    arbolCategorias: Categoria[] = [];
    mostrarFormulario = false;
    modoEdicion = false;
    cargandoCategorias = true;  // Estado de carga

    categoriaActual: Categoria = this.nuevaCategoria();

    // Wizard steps
    pasoActual = 1;
    totalPasos = 3;

    // Datos para subcategorías
    categoriasDisponibles: Categoria[] = []; // Para selección de padre
    nuevasSubcategorias: Partial<Categoria>[] = [];

    // Vista
    vistaActual: 'lista' | 'arbol' = 'arbol';
    expandidos: Set<number> = new Set();

    constructor(
        private apiService: ApiService,
        private authService: AuthService,
        private router: Router,
        private cdr: ChangeDetectorRef
    ) { }

    ngOnInit() {
        if (!this.authService.isLoggedIn()) {
            this.router.navigate(['/admin/login']);
            return;
        }
        this.loadCategorias();
        this.loadArbolCategorias();
    }

    nuevaCategoria(): Categoria {
        return {
            nombre: '',
            descripcion: '',
            orden: 0,
            activa: true,
            categoria_padre_id: null
        };
    }

    loadCategorias() {
        this.cargandoCategorias = true;
        this.apiService.get('/categorias?ver_todo=true').subscribe({
            next: (data: Categoria[]) => {
                this.categorias = data;
                // Categorías que pueden ser padres (nivel 1 y 2)
                // Primero asignamos para que getCategoriaPadreLabel funcione
                this.categoriasDisponibles = data.filter(c => (c.nivel || 1) < 3);
                // Luego ordenamos según la ruta completa
                this.categoriasDisponibles.sort((a, b) => {
                    const labelA = this.getCategoriaPadreLabel(a);
                    const labelB = this.getCategoriaPadreLabel(b);
                    return labelA.localeCompare(labelB);
                });
                this.cargandoCategorias = false;
                this.cdr.detectChanges();
            },
            error: (error: any) => {
                console.error('Error al cargar categorías:', error);
                alert('Error al cargar categorías');
                this.cargandoCategorias = false;
                this.cdr.detectChanges();
            }
        });
    }

    loadArbolCategorias() {
        this.cargandoCategorias = true;
        this.apiService.get('/categorias/tree').subscribe({
            next: (data: Categoria[]) => {
                this.arbolCategorias = data;
                this.cargandoCategorias = false;
                this.cdr.detectChanges();
            },
            error: (error: any) => {
                console.error('Error al cargar árbol:', error);
                this.cargandoCategorias = false;
                this.cdr.detectChanges();
            }
        });
    }

    nueva() {
        this.categoriaActual = this.nuevaCategoria();
        this.nuevasSubcategorias = [];
        this.pasoActual = 1;
        this.modoEdicion = false;
        this.mostrarFormulario = true;
    }

    editar(categoria: Categoria) {
        this.categoriaActual = { ...categoria };
        this.modoEdicion = true;
        this.pasoActual = 1;
        this.mostrarFormulario = true;
    }

    siguientePaso() {
        if (this.pasoActual < this.totalPasos) {
            this.pasoActual++;
        }
    }

    pasoAnterior() {
        if (this.pasoActual > 1) {
            this.pasoActual--;
        }
    }

    agregarNuevaSubcategoria() {
        this.nuevasSubcategorias.push({
            nombre: '',
            descripcion: '',
            orden: this.nuevasSubcategorias.length,
            activa: true
        });
    }

    eliminarNuevaSubcategoria(index: number) {
        this.nuevasSubcategorias.splice(index, 1);
    }

    guardar() {
        if (!this.categoriaActual.nombre.trim()) {
            alert('El nombre es requerido');
            return;
        }

        const payload: any = {
            nombre: this.categoriaActual.nombre,
            descripcion: this.categoriaActual.descripcion,
            imagen: this.categoriaActual.imagen,
            orden: this.categoriaActual.orden,
            categoria_padre_id: this.categoriaActual.categoria_padre_id,
            activa: this.categoriaActual.activa
        };

        // Agregar nuevas subcategorías
        if (this.nuevasSubcategorias.length > 0) {
            payload.subcategorias_nuevas = this.nuevasSubcategorias.filter(s => s.nombre && s.nombre.trim());
        }

        const request = this.modoEdicion
            ? this.apiService.put(`/admin/categorias/${this.categoriaActual.id}`, payload)
            : this.apiService.post('/admin/categorias', payload);

        request.subscribe({
            next: (data: any) => {
                alert(this.modoEdicion ? 'Categoría actualizada' : 'Categoría creada exitosamente');
                this.cancelar();
                this.loadCategorias();
                this.loadArbolCategorias();
            },
            error: (error: any) => {
                console.error('Error al guardar:', error);
                alert(error.error?.error || 'Error al guardar categoría');
            }
        });
    }

    eliminar(categoria: Categoria) {
        if (!confirm(`¿Eliminar categoría "${categoria.nombre}"?`)) {
            return;
        }

        this.apiService.deleteCategoria(categoria.id!).subscribe({
            next: () => {
                alert('Categoría eliminada');
                this.loadCategorias();
                this.loadArbolCategorias();
            },
            error: (error: any) => {
                // Check if it's the "has products" error
                if (error.status === 400 && error.error?.error?.includes('producto(s) asociado(s)')) {
                    if (confirm(`⚠️ ${error.error.error}\n\n¿Deseas ELIMINAR TODO (categoría + productos) permanentemente?`)) {
                        this.forceDelete(categoria.id!);
                    }
                } else {
                    console.error('Error al eliminar:', error);
                    alert(error.error?.error || 'Error al eliminar categoría');
                }
            }
        });
    }

    forceDelete(id: number) {
        this.apiService.deleteCategoria(id, true).subscribe({
            next: (response: any) => {
                alert(response.message || 'Categoría y productos eliminados correctamente');
                this.loadCategorias();
                this.loadArbolCategorias();
            },
            error: (error: any) => {
                console.error('Error al forzar eliminación:', error);
                alert('Error crítico al eliminar');
            }
        });
    }

    cancelar() {
        this.mostrarFormulario = false;
        this.categoriaActual = this.nuevaCategoria();
        this.nuevasSubcategorias = [];
        this.pasoActual = 1;
    }

    toggleExpand(id: number) {
        if (this.expandidos.has(id)) {
            this.expandidos.delete(id);
        } else {
            this.expandidos.add(id);
        }
    }

    isExpandido(id: number): boolean {
        return this.expandidos.has(id);
    }

    getNivelClass(nivel: number): string {
        return nivel === 1 ? 'nivel-1' : nivel === 2 ? 'nivel-2' : 'nivel-3';
    }

    getCategoriaPadreNombre(categoriaPadreId: number | null | undefined): string {
        if (!categoriaPadreId) return '-';
        const padre = this.categorias.find(c => c.id === categoriaPadreId);
        return padre ? padre.nombre : '-';
    }

    getCategoriaPadreLabel(cat: Categoria): string {
        if (!cat.categoria_padre_id) {
            return cat.nombre;
        }

        const padre = this.categorias.find(c => c.id === cat.categoria_padre_id);
        if (padre) {
            return `${this.getCategoriaPadreLabel(padre)} > ${cat.nombre}`;
        }

        return cat.nombre;
    }

    getCategoriaActualNivel(): number {
        if (!this.categoriaActual.categoria_padre_id) return 1;

        const padre = this.categorias.find(c => c.id === this.categoriaActual.categoria_padre_id);
        if (!padre) return 1;

        return (padre.nivel || 1) + 1;
    }

    volverAlPanel() {
        this.router.navigate(['/admin/gestion']);
    }
}
