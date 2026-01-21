import { Injectable } from '@angular/core';
import { Router } from '@angular/router';
import { ApiService } from './api.service';
import { BehaviorSubject, Observable, tap } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private isAuthenticatedSubject = new BehaviorSubject<boolean>(this.isLoggedIn());
  public isAuthenticated$ = this.isAuthenticatedSubject.asObservable();
  private inactivityTimer: any = null;
  private readonly INACTIVITY_TIMEOUT = 60 * 60 * 1000; // 1 hora en milisegundos

  constructor(
    private apiService: ApiService,
    private router: Router
  ) {
    this.checkAuth();
    this.setupInactivityTimer();
  }

  login(username: string, password: string): Observable<any> {
    return this.apiService.login(username, password).pipe(
      tap((response) => {
        localStorage.setItem('token', response.access_token);
        localStorage.setItem('admin', JSON.stringify(response.admin));
        localStorage.removeItem('cliente'); // Asegurar única sesión
        localStorage.setItem('lastActivity', Date.now().toString());
        this.isAuthenticatedSubject.next(true);
        this.resetInactivityTimer();
      })
    );
  }

  loginUnified(identifier: string, password: string): Observable<any> {
    return this.apiService.loginUnified({ identifier, password }).pipe(
      tap((response) => {
        localStorage.setItem('token', response.access_token);
        localStorage.setItem('lastActivity', Date.now().toString());

        if (response.user_type === 'admin') {
          localStorage.setItem('admin', JSON.stringify(response.admin));
          localStorage.removeItem('cliente');
        } else {
          localStorage.setItem('cliente', JSON.stringify(response.cliente));
          localStorage.removeItem('admin');
        }

        this.isAuthenticatedSubject.next(true);
        this.resetInactivityTimer();
      })
    );
  }

  loginCliente(email: string, password: string): Observable<any> {
    return new Observable(observer => {
      this.apiService.loginCliente({ email, password }).subscribe({
        next: (response) => {
          localStorage.setItem('token', response.access_token);
          localStorage.setItem('cliente', JSON.stringify(response.cliente));
          localStorage.removeItem('admin'); // Asegurar única sesión
          localStorage.setItem('lastActivity', Date.now().toString());
          this.isAuthenticatedSubject.next(true);
          this.resetInactivityTimer();
          observer.next(response);
          observer.complete();
        },
        error: (error) => {
          observer.error(error);
        }
      });
    });
  }

  requestPasswordReset(email: string): Observable<any> {
    return this.apiService.post('/auth/forgot-password', { email });
  }

  resetPassword(token: string, password: string): Observable<any> {
    return this.apiService.post('/auth/reset-password', { token, password });
  }

  logout(): void {
    localStorage.removeItem('token');
    localStorage.removeItem('admin');
    localStorage.removeItem('cliente');
    localStorage.removeItem('lastActivity');
    this.isAuthenticatedSubject.next(false);
    this.clearInactivityTimer();
    this.router.navigate(['/']);
  }

  isLoggedIn(): boolean {
    return !!localStorage.getItem('token');
  }

  getToken(): string | null {
    return localStorage.getItem('token');
  }

  getAdmin(): any {
    const admin = localStorage.getItem('admin');
    return admin ? JSON.parse(admin) : null;
  }

  getCliente(): any {
    const cliente = localStorage.getItem('cliente');
    return cliente ? JSON.parse(cliente) : null;
  }

  private checkAuth(): void {
    if (this.isLoggedIn()) {
      // Verificar inactividad
      const lastActivity = localStorage.getItem('lastActivity');
      if (lastActivity) {
        const timeSinceActivity = Date.now() - parseInt(lastActivity);
        if (timeSinceActivity > this.INACTIVITY_TIMEOUT) {
          this.logout();
          return;
        }
      }

      const isAdmin = !!localStorage.getItem('admin');
      const isCliente = !!localStorage.getItem('cliente');

      if (isAdmin) {
        this.apiService.verifyToken().subscribe({
          next: () => {
            this.isAuthenticatedSubject.next(true);
            this.resetInactivityTimer();
          },
          error: () => this.logout()
        });
      } else if (isCliente) {
        this.apiService.verifyTokenCliente().subscribe({
          next: () => {
            this.isAuthenticatedSubject.next(true);
            this.resetInactivityTimer();
          },
          error: () => this.logout()
        });
      } else {
        this.logout();
      }
    }
  }

  private setupInactivityTimer(): void {
    const events = ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart', 'click'];
    events.forEach(event => {
      document.addEventListener(event, () => {
        if (this.isLoggedIn()) {
          localStorage.setItem('lastActivity', Date.now().toString());
          this.resetInactivityTimer();
        }
      }, true);
    });
  }

  private resetInactivityTimer(): void {
    this.clearInactivityTimer();
    if (this.isLoggedIn()) {
      this.inactivityTimer = setTimeout(() => {
        const lastActivity = localStorage.getItem('lastActivity');
        if (lastActivity) {
          const timeSinceActivity = Date.now() - parseInt(lastActivity);
          if (timeSinceActivity >= this.INACTIVITY_TIMEOUT) {
            alert('Tu sesión ha expirado por inactividad.');
            this.logout();
          }
        }
      }, this.INACTIVITY_TIMEOUT);
    }
  }

  private clearInactivityTimer(): void {
    if (this.inactivityTimer) {
      clearTimeout(this.inactivityTimer);
      this.inactivityTimer = null;
    }
  }
}
