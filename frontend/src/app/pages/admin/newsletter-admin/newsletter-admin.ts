import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../../../environments/environment';
import { ToastService } from '../../../services/toast.service';
import { QuillModule } from 'ngx-quill';

@Component({
    selector: 'app-newsletter-admin',
    standalone: true,
    imports: [CommonModule, FormsModule, QuillModule],
    templateUrl: './newsletter-admin.html',
    styleUrl: './newsletter-admin.css'
})
export class NewsletterAdminComponent {
    subject: string = '';
    content: string = '';
    testEmail: string = '';

    isLoading: boolean = false;
    lastStats: any = null;

    private apiUrl = environment.apiUrl;

    constructor(
        private http: HttpClient,
        private toastService: ToastService
    ) { }

    send(isTest: boolean = true) {
        if (!this.subject || !this.content) {
            this.toastService.show('Asunto y Mensaje son requeridos', 'error');
            return;
        }

        if (isTest && !this.testEmail) {
            this.toastService.show('Ingresá un email para probar', 'error');
            return;
        }

        if (!isTest && !confirm('¿Estás seguro de enviar este newsletter a TODOS los suscriptores? Esta acción no se puede deshacer.')) {
            return;
        }

        this.isLoading = true;
        this.lastStats = null;

        const payload = {
            subject: this.subject,
            content: this.content, // En el futuro podremos usar un editor HTML
            test_email: isTest ? this.testEmail : null
        };

        const token = localStorage.getItem('token');

        this.http.post(`${this.apiUrl}/admin/newsletter/send`, payload, {
            headers: { 'Authorization': `Bearer ${token}` }
        }).subscribe({
            next: (res: any) => {
                this.isLoading = false;
                this.toastService.show(res.message, 'success');
                this.lastStats = res;
            },
            error: (err) => {
                this.isLoading = false;
                console.error('Error enviando newsletter:', err);
                const msg = err.error?.error || 'Error al enviar newsletter';
                this.toastService.show(msg, 'error');
            }
        });
    }
}
