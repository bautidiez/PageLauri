import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule, FormsModule } from '@angular/forms';
import { Router, RouterModule } from '@angular/router';
import { CartService } from '../../services/cart.service';
import { CheckoutService } from '../../services/checkout.service';

@Component({
    selector: 'app-checkout-v2',
    standalone: true,
    imports: [CommonModule, ReactiveFormsModule, FormsModule, RouterModule],
    templateUrl: './checkout-v2.html',
    styleUrl: './checkout-v2.css'
})
export class CheckoutV2Component implements OnInit {
    currentStep = 1;
    items: any[] = [];
    total = 0;

    // Forms
    datosForm: FormGroup;
    envioForm: FormGroup;
    pagoForm: FormGroup;
    couponForm: FormGroup;

    // Data from backend
    shippingOptions: any[] = [];
    transferData: any = null;
    loading = false;
    orderCreated: any = null;
    appliedCoupon: any = null;
    couponError: string = '';
    couponSuccess: string = '';
    validatingCoupon = false;

    constructor(
        private fb: FormBuilder,
        private cartService: CartService,
        private checkoutService: CheckoutService,
        private router: Router
    ) {
        this.datosForm = this.fb.group({
            email: ['', [Validators.required, Validators.email]],
            codigo_postal: ['', [Validators.required, Validators.minLength(4)]],
            nombre: ['', [Validators.required, Validators.minLength(2)]],
            apellido: ['', [Validators.required, Validators.minLength(2)]],
            telefono: ['', [Validators.required]],
            calle: ['', [Validators.required]],
            altura: ['', [Validators.required]],
            piso: [''],
            ciudad: ['', [Validators.required]],
            // provincia: Eliminado duplicado si existía
            provincia: ['', [Validators.required]],
            dni: ['', [Validators.required, Validators.minLength(7)]]
        });

        this.envioForm = this.fb.group({
            metodo_id: ['', Validators.required]
        });

        this.pagoForm = this.fb.group({
            metodo: ['', Validators.required],
            // Card data (simulated for UI)
            card_number: [''],
            card_name: [''],
            card_expiry: [''],
            card_cvv: [''],
            card_dni: ['']
        });

        this.couponForm = this.fb.group({
            code: ['', Validators.required]
        });
    }

    ngOnInit() {
        this.cartService.cart$.subscribe(items => {
            this.items = items;
            this.total = this.cartService.getTotal();
            if (this.items.length === 0 && !this.orderCreated) {
                this.router.navigate(['/carrito']);
            }
        });

        this.checkoutService.getDatosTransferencia().subscribe(data => {
            this.transferData = data;
        });
    }

    nextStep() {
        if (this.currentStep === 2) {
            // Validate that shipping is selected
            if (this.envioForm.invalid) {
                this.envioForm.markAllAsTouched();
                alert('Por favor selecciona una forma de envío');
                return;
            }
            // Validate personal data
            if (this.datosForm.invalid) {
                this.datosForm.markAllAsTouched();
                // Scroll to first error?
                return;
            }
        }
        this.currentStep++;
        window.scrollTo(0, 0);
    }

    prevStep() {
        this.currentStep--;
        window.scrollTo(0, 0);
    }

    calculateShipping() {
        const cp = this.datosForm.get('codigo_postal')?.value;
        if (cp) {
            this.loading = true;
            this.checkoutService.calcularEnvio(cp).subscribe({
                next: (options) => {
                    this.shippingOptions = options;
                    this.loading = false;
                },
                error: () => this.loading = false
            });
        }
    }

    getSelectedShipping() {
        const id = this.envioForm.get('metodo_id')?.value;
        return this.shippingOptions.find(o => o.id === id);
    }

    getFinalTotal() {
        const shipping = this.getSelectedShipping();
        const metodoPago = this.pagoForm.get('metodo')?.value;
        let total = this.total + (shipping ? shipping.costo : 0);

        // Descuento del 15% si es efectivo en el local
        if (metodoPago === 'efectivo_local') {
            return total * 0.85;
        }
        // Descuento del 15% si es transferencia
        if (metodoPago === 'transferencia') {
            return total * 0.85;
        }
        // Descuento del 15% si es efectivo (Rapipago)
        if (metodoPago === 'efectivo') {
            return total * 0.85;
        }

        // Aplicar cupón si existe
        if (this.appliedCoupon) {
            if (this.appliedCoupon.envio_gratis) {
                // Si es envío gratis, restar costo de envío (si hay)
                if (shipping) {
                    total -= shipping.costo;
                }
            } else if (this.appliedCoupon.tipo_promocion_nombre === 'descuento_porcentaje') {
                total -= (this.total * this.appliedCoupon.valor / 100);
            } else if (this.appliedCoupon.tipo_promocion_nombre === 'descuento_fijo') {
                total -= this.appliedCoupon.valor;
            }
        }

        return Math.max(0, total);
    }

    validateCoupon() {
        if (this.couponForm.invalid) return;

        const code = this.couponForm.get('code')?.value;
        this.validatingCoupon = true;
        this.couponError = '';
        this.couponSuccess = '';

        this.checkoutService.validarCupon(code).subscribe({
            next: (cupon) => {
                this.appliedCoupon = cupon;
                this.couponSuccess = `¡Cupón ${code} aplicado exitosamente!`;
                this.validatingCoupon = false;
                this.couponForm.reset();
            },
            error: (err) => {
                this.couponError = err.error?.error || 'Error al validar el cupón';
                this.validatingCoupon = false;
                this.appliedCoupon = null;
            }
        });
    }

    finalizarCompra() {
        if (this.datosForm.invalid || this.pagoForm.invalid) {
            this.datosForm.markAllAsTouched();
            this.pagoForm.markAllAsTouched();
            return;
        }

        const shipping = this.getSelectedShipping();
        const datos = this.datosForm.value;
        const pedidoData = {
            cliente_nombre: `${datos.nombre} ${datos.apellido}`, // Concatenate for backend compatibility
            cliente_email: datos.email,
            cliente_telefono: datos.telefono,
            calle: datos.calle,
            altura: datos.altura,
            piso: datos.piso,
            ciudad: datos.ciudad,
            provincia: datos.provincia,
            codigo_postal: datos.codigo_postal,

            metodo_envio: shipping?.nombre,
            costo_envio: shipping?.costo,
            metodo_pago: this.pagoForm.get('metodo')?.value,

            items: this.items.map(i => ({
                producto_id: i.producto.id,
                talle_id: i.talle.id,
                cantidad: i.cantidad,
                precio_unitario: i.precio_unitario
            })),
            subtotal: this.total,
            total: this.getFinalTotal()
        };

        this.loading = true;
        this.checkoutService.crearPedido(pedidoData).subscribe({
            next: (order) => {
                this.orderCreated = order;
                this.loading = false;
                this.cartService.clearCart();
                this.currentStep = 4; // Success is now Step 4 (was 5)
            },
            error: (err) => {
                alert("Error al crear el pedido: " + err.message);
                this.loading = false;
            }
        });
    }
}
