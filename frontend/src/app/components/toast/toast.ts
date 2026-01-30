import { Component, OnDestroy, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ToastService, ToastData } from '../../services/toast.service';
import { Subscription } from 'rxjs';

@Component({
    selector: 'app-toast',
    standalone: true,
    imports: [CommonModule],
    templateUrl: './toast.html',
    styleUrl: './toast.css'
})
export class ToastComponent implements OnInit, OnDestroy {
    show = false;
    message = '';
    type: 'success' | 'error' | 'info' = 'info';
    private subscription!: Subscription;
    private timeoutId: any;

    constructor(private toastService: ToastService) { }

    ngOnInit() {
        this.subscription = this.toastService.toastState.subscribe((data: ToastData) => {
            this.message = data.message;
            this.type = data.type;
            this.show = true;

            // Clear existing timeout
            if (this.timeoutId) {
                clearTimeout(this.timeoutId);
            }

            // Auto hide
            this.timeoutId = setTimeout(() => {
                this.close();
            }, data.duration || 3000);
        });
    }

    close() {
        this.show = false;
    }

    ngOnDestroy() {
        if (this.subscription) {
            this.subscription.unsubscribe();
        }
    }
}
