import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule, Router } from '@angular/router';
import { AuthService } from '../../../services/auth.service';
import { ApiService } from '../../../services/api.service';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, RouterModule],
  templateUrl: './dashboard.html',
  styleUrl: './dashboard.css',
})

export class DashboardComponent implements OnInit {
  estadisticas: any = null;
  estadisticasVentas: any = null;
  loading = true;
  loadingVentas = false;
  isAuthenticated = false;
  errorMessage = ''; // Para mostrar el error en pantalla
  periodoSeleccionado = 'dia'; // dia, semana, mes, anio
  anioSeleccionado = new Date().getFullYear();
  mesSeleccionado = new Date().getMonth() + 1;
  aniosDisponibles: number[] = [];
  mesesDisponibles = [
    { id: 1, nombre: 'Enero' }, { id: 2, nombre: 'Febrero' }, { id: 3, nombre: 'Marzo' },
    { id: 4, nombre: 'Abril' }, { id: 5, nombre: 'Mayo' }, { id: 6, nombre: 'Junio' },
    { id: 7, nombre: 'Julio' }, { id: 8, nombre: 'Agosto' }, { id: 9, nombre: 'Septiembre' },
    { id: 10, nombre: 'Octubre' }, { id: 11, nombre: 'Noviembre' }, { id: 12, nombre: 'Diciembre' }
  ];

  currentDate = new Date(); // Fecha de referencia para la navegación

  constructor(
    private authService: AuthService,
    private apiService: ApiService,
    private router: Router,
    private cdr: ChangeDetectorRef
  ) { }

  ngOnInit() {
    // Verificar autenticación de forma síncrona primero
    if (!this.authService.isLoggedIn()) {
      this.router.navigate(['/admin/login']);
      return;
    }

    this.isAuthenticated = true;
    this.generarAniosDisponibles();
    this.loadEstadisticas();
    this.loadEstadisticasVentas();

    // Suscribirse para cambios futuros
    this.authService.isAuthenticated$.subscribe(isAuth => {
      this.isAuthenticated = isAuth;
      if (!isAuth) {
        this.router.navigate(['/admin/login']);
      }
    });
  }

  loadEstadisticas() {
    // No mostrar loading si ya hay datos
    if (!this.estadisticas) {
      this.loading = true;
    }
    this.apiService.getEstadisticas().subscribe({
      next: (data) => {
        this.estadisticas = data;
        this.loading = false;
        this.cdr.detectChanges();
      },
      error: (error) => {
        console.error('Error cargando estadísticas:', error);
        this.loading = false;

        if (error.status === 500) {
          this.errorMessage = `Error del servidor: ${error.error?.error || error.message || 'Desconocido'}`;
        } else {
          this.errorMessage = `Error de conexión: ${error.status} ${error.statusText}`;
        }

        this.cdr.detectChanges();
      }
    });
  }

  loadEstadisticasVentas() {
    this.loadingVentas = true;
    const anio = (this.periodoSeleccionado === 'mes' || this.periodoSeleccionado === 'dia') ? this.anioSeleccionado : undefined;
    const mes = (this.periodoSeleccionado === 'dia') ? this.mesSeleccionado : undefined;

    // Convertir fecha a string YYYY-MM-DD
    const fechaRefStr = this.currentDate.toISOString().split('T')[0];

    this.apiService.getEstadisticasVentas(this.periodoSeleccionado, anio, mes, fechaRefStr).subscribe({
      next: (data) => {
        this.estadisticasVentas = data;
        this.loadingVentas = false;
        this.cdr.detectChanges();
      },
      error: (error) => {
        console.error('Error cargando estadísticas de ventas:', error);
        this.loadingVentas = false;
        this.estadisticasVentas = null;
        this.cdr.detectChanges();
      }
    });
  }

  // Como no puedo modificar api.service.ts en el mismo paso que este sin romper la compilación si typescript es estricto,
  // hare la modificación del api call mas abajo para pasar fecha_referencia.

  cambiarPeriodo(periodo: string) {
    this.periodoSeleccionado = periodo;
    this.currentDate = new Date(); // Resetear a hoy al cambiar periodo mayor
    this.loadEstadisticasVentas();
  }

  paginarAtras() {
    if (this.periodoSeleccionado === 'dia') {
      this.currentDate.setDate(this.currentDate.getDate() - 7);
    } else if (this.periodoSeleccionado === 'semana') {
      this.currentDate.setDate(this.currentDate.getDate() - 7); // Moverse 1 semana en el view de 8? O moverse el bloque entero?
      // El usuario pide "volver atras para ver graficas pasadas".
      // Si mostramos 8 semanas, volver atras podria ser mover la fecha de referencia 1 semana atras o 8.
      // Moveremos 1 semana para desplazamiento suave.
      this.currentDate.setDate(this.currentDate.getDate() - 7);
    } else if (this.periodoSeleccionado === 'mes') {
      this.anioSeleccionado--; // En vista mensual, "atras" mueve el año
    } else if (this.periodoSeleccionado === 'anio') {
      // Nada, se muestran todos los años
    }
    this.loadEstadisticasVentas();
  }

  paginarAdelante() {
    const hoy = new Date();
    if (this.periodoSeleccionado === 'dia') {
      this.currentDate.setDate(this.currentDate.getDate() + 7);
    } else if (this.periodoSeleccionado === 'semana') {
      this.currentDate.setDate(this.currentDate.getDate() + 7);
    } else if (this.periodoSeleccionado === 'mes') {
      this.anioSeleccionado++;
    }

    // No permitir ir al futuro más allá de esta semana/año razonablemente
    if (this.currentDate > hoy) {
      this.currentDate = hoy;
    }
    if (this.anioSeleccionado > hoy.getFullYear()) {
      this.anioSeleccionado = hoy.getFullYear();
    }

    this.loadEstadisticasVentas();
  }

  cambiarAnio(anio: any) {
    this.anioSeleccionado = parseInt(anio.target.value);
    this.loadEstadisticasVentas();
  }

  cambiarMes(mes: any) {
    this.mesSeleccionado = parseInt(mes.target.value);
    this.loadEstadisticasVentas();
  }

  generarAniosDisponibles() {
    const anioActual = new Date().getFullYear();
    // Ahora dependemos del backend para esto en modo 'año', pero para los selects mantenemos logica local o usamos data del backend?
    // El backend en modo 'año' devuelve los intervalos.
    // Podemos seguir generando una lista estatica para los selects de historial meses.
    for (let a = 2024; a <= anioActual; a++) {
      if (!this.aniosDisponibles.includes(a)) {
        this.aniosDisponibles.push(a);
      }
    }
  }

  logout() {
    this.authService.logout();
  }

  goToPanelGestion() {
    this.router.navigate(['/admin/gestion']);
  }

  goToGestionProductos() {
    this.router.navigate(['/admin/productos']);
  }

  goToGestionCategorias() {
    this.router.navigate(['/admin/categorias']);
  }

  goToGestionPedidos() {
    this.router.navigate(['/admin/pedidos']);
  }

  goToGestionStock() {
    this.router.navigate(['/admin/stock']);
  }

  goToGestionPromociones() {
    this.router.navigate(['/admin/promociones']);
  }

  getVentaMaxima(): any {
    if (!this.estadisticasVentas || !this.estadisticasVentas.datos) return null;
    return this.estadisticasVentas.datos.reduce((max: any, item: any) =>
      item.ventas > max.ventas ? item : max, this.estadisticasVentas.datos[0]);
  }

  getVentaMinima(): any {
    if (!this.estadisticasVentas || !this.estadisticasVentas.datos) return null;
    return this.estadisticasVentas.datos.reduce((min: any, item: any) =>
      item.ventas < min.ventas ? item : min, this.estadisticasVentas.datos[0]);
  }
}
