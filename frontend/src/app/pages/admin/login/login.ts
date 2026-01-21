import { Component, ChangeDetectorRef, NgZone } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterModule, Router } from '@angular/router';
import { AuthService } from '../../../services/auth.service';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule],
  templateUrl: './login.html',
  styleUrl: './login.css',
})
export class LoginComponent {
  username = '';
  password = '';
  error = '';
  loading = false;
  constructor(
    private authService: AuthService,
    private router: Router,
    private cdr: ChangeDetectorRef,
    private zone: NgZone
  ) { }

  login() {
    if (!this.username || !this.password) {
      this.error = 'Por favor completa todos los campos';
      return;
    }

    this.loading = true;
    this.error = '';

    this.authService.loginUnified(this.username, this.password).subscribe({
      next: (response) => {
        if (response.user_type === 'admin') {
          this.router.navigate(['/admin']);
        } else {
          this.router.navigate(['/']); // Redirigir a inicio si por alguna razón entra un cliente aquí
        }
      },
      error: (err) => {
        this.zone.run(() => {
          console.error('Error en login:', err);
          this.error = 'Credenciales incorrectas';
          this.loading = false;
          this.cdr.detectChanges();
        });
      }
    });
  }
}
