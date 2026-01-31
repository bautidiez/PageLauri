import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule, Router } from '@angular/router';
import { AuthService } from '../../../services/auth.service';

@Component({
  selector: 'app-gestion',
  standalone: true,
  imports: [CommonModule, RouterModule],
  templateUrl: './gestion.html',
  styleUrl: './gestion.css'
})
export class GestionComponent implements OnInit {
  isAuthenticated = false;

  constructor(
    private authService: AuthService,
    private router: Router
  ) { }

  ngOnInit() {
    this.authService.isAuthenticated$.subscribe(isAuth => {
      this.isAuthenticated = isAuth;
      if (!isAuth) {
        this.router.navigate(['/admin/login']);
      }
    });
  }

  goToProductos() {
    this.router.navigate(['/admin/productos']);
  }

  goToCategorias() {
    this.router.navigate(['/admin/categorias']);
  }

  goToPedidos() {
    this.router.navigate(['/admin/pedidos']);
  }

  goToStock() {
    this.router.navigate(['/admin/stock']);
  }

  goToPromociones() {
    this.router.navigate(['/admin/promociones']);
  }

  goToNewsletter() {
    this.router.navigate(['/admin/newsletter']);
  }

  goToPanelPrincipal() {
    this.router.navigate(['/admin']);
  }
}
