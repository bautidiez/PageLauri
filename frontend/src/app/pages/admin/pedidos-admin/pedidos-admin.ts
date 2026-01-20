import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterModule, Router, ActivatedRoute } from '@angular/router';
import { ApiService } from '../../../services/api.service';
import { AuthService } from '../../../services/auth.service';

interface NotaPedido {
  id: number;
  pedido_id: number;
  admin_id: number;
  admin_username: string;
  contenido: string;
  created_at: string;
}

interface Pedido {
  id: number;
  numero_pedido: string;
  cliente_nombre: string;
  cliente_email: string;
  cliente_telefono?: string;
  cliente_direccion: string;
  cliente_codigo_postal: string;
  cliente_localidad: string;
  cliente_provincia: string;
  estado: string;
  subtotal: number;
  descuento: number;
  costo_envio: number;
  total: number;
  aprobado: boolean;
  fecha_expiracion?: string;
  fecha_aprobacion?: string;
  admin_aprobador_id?: number;
  admin_aprobador_username?: string;
  created_at: string;
  updated_at: string;
  items: any[];
  notas?: string; // notas legacy (campo texto)
}

@Component({
  selector: 'app-pedidos-admin',
  imports: [CommonModule, FormsModule, RouterModule],
  templateUrl: './pedidos-admin.html',
  styleUrl: './pedidos-admin.css'
})
export class PedidosAdminComponent implements OnInit {
  pedidos: Pedido[] = [];
  pedidoSeleccionado: Pedido | null = null;
  loading = true;

  // Filtros
  filtroEstado = '';
  busquedaCliente = '';
  estados = ['pendiente_aprobacion', 'confirmado', 'en_preparacion', 'enviado', 'entregado', 'cancelado'];

  // Estado del pedido
  nuevoEstado = '';

  // Sistema de notas internas
  notasInternas: NotaPedido[] = [];
  nuevaNota = '';
  loadingNotas = false;

  constructor(
    private apiService: ApiService,
    private authService: AuthService,
    private router: Router,
    private route: ActivatedRoute,
    private cdr: ChangeDetectorRef
  ) { }

  ngOnInit() {
    if (!this.authService.isLoggedIn()) {
      this.router.navigate(['/admin/login']);
      return;
    }
    this.loadPedidos();
  }

  loadPedidos() {
    if (this.pedidos.length === 0) {
      this.loading = true;
    }
    this.apiService.getPedidos(this.filtroEstado || undefined).subscribe({
      next: (response: any) => {
        // Si viene paginado
        if (response.items) {
          this.pedidos = response.items;
        } else {
          this.pedidos = response;
        }
        this.loading = false;
        this.cdr.detectChanges();
      },
      error: (error: any) => {
        console.error('Error cargando pedidos:', error);
        this.loading = false;
        this.cdr.detectChanges();
      }
    });
  }

  get pedidosFiltrados(): Pedido[] {
    if (!this.busquedaCliente.trim()) {
      return this.pedidos;
    }
    const termino = this.busquedaCliente.toLowerCase();
    return this.pedidos.filter(p =>
      p.cliente_nombre.toLowerCase().includes(termino) ||
      p.numero_pedido.toLowerCase().includes(termino) ||
      p.cliente_email.toLowerCase().includes(termino)
    );
  }

  filtrarPorEstado() {
    this.loadPedidos();
  }

  limpiarFiltros() {
    this.filtroEstado = '';
    this.busquedaCliente = '';
    this.loadPedidos();
  }

  verDetalle(pedido: Pedido) {
    this.apiService.getPedido(pedido.id).subscribe({
      next: (data: Pedido) => {
        this.pedidoSeleccionado = data;
        this.nuevoEstado = data.estado;
        this.loadNotasInternas(pedido.id);
        this.cdr.detectChanges();
      },
      error: (error: any) => {
        console.error('Error cargando detalle:', error);
        alert('Error al cargar detalle del pedido');
        this.cdr.detectChanges();
      }
    });
  }

  loadNotasInternas(pedidoId: number) {
    this.loadingNotas = true;
    this.apiService.get(`/admin/pedidos/${pedidoId}/notas`).subscribe({
      next: (notas: NotaPedido[]) => {
        this.notasInternas = notas;
        this.loadingNotas = false;
        this.cdr.detectChanges();
      },
      error: (error: any) => {
        console.error('Error cargando notas:', error);
        this.loadingNotas = false;
        this.cdr.detectChanges();
      }
    });
  }

  agregarNota() {
    if (!this.pedidoSeleccionado || !this.nuevaNota.trim()) {
      return;
    }

    this.apiService.post(`/admin/pedidos/${this.pedidoSeleccionado.id}/notas`, {
      contenido: this.nuevaNota
    }).subscribe({
      next: (nota: NotaPedido) => {
        this.notasInternas.unshift(nota); // Agregar al inicio
        this.nuevaNota = '';
        alert('Nota agregada exitosamente');
      },
      error: (error: any) => {
        console.error('Error agregando nota:', error);
        alert('Error al agregar nota');
      }
    });
  }

  eliminarNota(notaId: number) {
    if (!confirm('¿Eliminar esta nota?')) {
      return;
    }

    this.apiService.delete(`/admin/notas/${notaId}`).subscribe({
      next: () => {
        this.notasInternas = this.notasInternas.filter(n => n.id !== notaId);
        alert('Nota eliminada');
      },
      error: (error: any) => {
        console.error('Error eliminando nota:', error);
        alert('Error al eliminar nota');
      }
    });
  }

  actualizarEstado() {
    if (!this.pedidoSeleccionado) return;

    const actualizacion = {
      estado: this.nuevoEstado
    };

    this.apiService.updatePedido(this.pedidoSeleccionado.id, actualizacion).subscribe({
      next: () => {
        alert('Estado actualizado exitosamente');
        this.loadPedidos();
        if (this.pedidoSeleccionado) {
          this.pedidoSeleccionado.estado = this.nuevoEstado;
        }
      },
      error: (error: any) => {
        alert('Error al actualizar estado');
        console.error(error);
      }
    });
  }

  cerrarDetalle() {
    this.pedidoSeleccionado = null;
    this.notasInternas = [];
    this.nuevaNota = '';
  }

  aprobarPedido(pedido: Pedido) {
    if (!confirm(`¿Aprobar el pedido ${pedido.numero_pedido}?\n\nEsto reducirá el stock y procesará el pedido.`)) {
      return;
    }

    this.apiService.aprobarPedido(pedido.id).subscribe({
      next: (response: any) => {
        alert('✅ ' + response.message);
        this.loadPedidos();
        if (this.pedidoSeleccionado && this.pedidoSeleccionado.id === pedido.id) {
          this.pedidoSeleccionado = response.pedido;
        }
        this.cdr.detectChanges();
      },
      error: (error: any) => {
        alert('❌ Error: ' + (error.error?.error || 'No se pudo aprobar el pedido'));
        console.error(error);
      }
    });
  }

  getDiasRestantes(fecha_expiracion: string): number {
    if (!fecha_expiracion) return 0;
    const ahora = new Date().getTime();
    const expira = new Date(fecha_expiracion).getTime();
    const diff = expira - ahora;
    return Math.ceil(diff / (1000 * 60 * 60 * 24));
  }

  isExpirando(pedido: Pedido): boolean {
    if (!pedido.fecha_expiracion || pedido.aprobado) return false;
    return this.getDiasRestantes(pedido.fecha_expiracion) <= 2;
  }

  getEstadoClass(estado: string): string {
    const clases: any = {
      'pendiente': 'estado-pendiente',
      'pendiente_aprobacion': 'estado-pendiente-aprobacion',
      'confirmado': 'estado-confirmado',
      'en_preparacion': 'estado-preparacion',
      'enviado': 'estado-enviado',
      'entregado': 'estado-entregado',
      'cancelado': 'estado-cancelado'
    };
    return clases[estado] || '';
  }

  getEstadoLabel(estado: string): string {
    const labels: any = {
      'pendiente': 'Pendiente',
      'pendiente_aprobacion': 'Pendiente de Aprobación',
      'confirmado': 'Confirmado',
      'en_preparacion': 'En Preparación',
      'enviado': 'Enviado',
      'entregado': 'Entregado',
      'cancelado': 'Cancelado'
    };
    return labels[estado] || estado;
  }

  formatFecha(fecha: string): string {
    if (!fecha) return '-';
    const d = new Date(fecha);
    return d.toLocaleDateString('es-AR') + ' ' + d.toLocaleTimeString('es-AR', { hour: '2-digit', minute: '2-digit' });
  }

  getTotalItems(pedido: Pedido): number {
    return pedido.items?.reduce((sum, item) => sum + item.cantidad, 0) || 0;
  }
}
