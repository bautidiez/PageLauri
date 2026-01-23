import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

@Injectable({
    providedIn: 'root'
})
export class CheckoutService {
    private apiUrl = environment.apiUrl;

    constructor(private http: HttpClient) { }

    // Cálculo de Envío
    calcularEnvio(codigo_postal: string): Observable<any[]> {
        return this.http.post<any[]>(`${this.apiUrl}/envios/calcular`, { codigo_postal });
    }

    // Gestión de Pedidos
    crearPedido(datosPedido: any): Observable<any> {
        return this.http.post<any>(`${this.apiUrl}/orders`, datosPedido);
    }

    getPedido(id: number): Observable<any> {
        return this.http.get<any>(`${this.apiUrl}/orders/${id}`);
    }

    getPedidosCliente(email: string): Observable<any[]> {
        return this.http.get<any[]>(`${this.apiUrl}/orders/by-customer/${email}`);
    }

    // Pagos
    getDatosTransferencia(): Observable<any> {
        return this.http.get<any>(`${this.apiUrl}/payments/transfer-data`);
    }

    confirmarTransferencia(orderId: number): Observable<any> {
        return this.http.post<any>(`${this.apiUrl}/payments/confirm-transfer/${orderId}`, {});
    }

    validarCupon(codigo: string): Observable<any> {
        return this.http.post<any>(`${this.apiUrl}/promociones/validar`, { codigo });
    }
}
