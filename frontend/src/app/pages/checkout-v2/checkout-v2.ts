import { Component, OnInit, ChangeDetectorRef, NgZone } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule, FormsModule } from '@angular/forms';
import { CartService } from '../../services/cart.service';
import { CheckoutService } from '../../services/checkout.service';
import { ApiService } from '../../services/api.service';
import { Router, RouterModule } from '@angular/router';
import { AuthService } from '../../services/auth.service';

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
        private apiService: ApiService,
        private authService: AuthService,
        private router: Router,
        private cdr: ChangeDetectorRef,
        private zone: NgZone
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

        this.prefillClientData();
        this.setupConditionalValidation();
    }

    prefillClientData() {
        const cliente = this.authService.getCliente();
        if (cliente) {
            this.datosForm.patchValue({
                email: cliente.email,
                nombre: cliente.nombre || '',
                apellido: cliente.apellido || '',
                telefono: cliente.telefono || '',
                codigo_postal: cliente.codigo_postal || '',
                calle: cliente.calle || '',
                altura: cliente.altura || '',
                piso: cliente.piso || '',
                ciudad: cliente.ciudad || '',
                provincia: cliente.provincia || '',
                dni: cliente.dni || ''
            });
        }
    }

    setupConditionalValidation() {
        this.envioForm.get('metodo_id')?.valueChanges.subscribe(id => {
            const isRetiro = this.isRetiro(id);
            const addressFields = ['calle', 'altura', 'ciudad', 'provincia'];

            addressFields.forEach(field => {
                const control = this.datosForm.get(field);
                if (isRetiro) {
                    control?.clearValidators();
                } else {
                    control?.setValidators([Validators.required]);
                }
                control?.updateValueAndValidity();
            });
        });
    }

    isRetiro(id?: string): boolean {
        const selectedId = id || this.envioForm.get('metodo_id')?.value;
        const options = this.getOpcionesRetiro();
        return options.some(opt => opt.id === selectedId);
    }

    getBaseTotal() {
        const shipping = this.getSelectedShipping();
        return this.total + (shipping ? shipping.costo : 0);
    }

    getDiscountedHeaderPrice(metodo: string) {
        const base = this.getBaseTotal();
        if (['transferencia', 'efectivo', 'efectivo_local'].includes(metodo)) {
            return base * 0.85;
        }
        return base;
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

    private isCalculatingShipping = false;

    calculateShipping() {
        console.log('DEBUG: calculateShipping triggered');
        if (this.isCalculatingShipping) return;

        const cp = this.datosForm.get('codigo_postal')?.value;
        if (cp && cp.length >= 4) {
            this.loading = true;
            this.isCalculatingShipping = true;
            this.checkoutService.calcularEnvio(cp).subscribe({
                next: (options) => {
                    this.zone.run(() => {
                        this.shippingOptions = options;
                        this.loading = false;
                        this.isCalculatingShipping = false;
                        this.cdr.markForCheck();
                        this.cdr.detectChanges();
                    });
                },
                error: (err) => {
                    this.zone.run(() => {
                        this.loading = false;
                        this.isCalculatingShipping = false;
                        console.error('Error calculando envío', err);
                        this.cdr.detectChanges();
                    });
                }
            });
        }
    }

    getSelectedShipping() {
        const id = this.envioForm.get('metodo_id')?.value;
        return this.shippingOptions.find(o => o.id === id);
    }

    getOpcionesDomicilio() {
        return this.shippingOptions.filter(o => {
            const name = o.nombre.toLowerCase();
            const isHomeKeyword = name.includes('domicilio') || name.includes('estándar') || name.includes('envío') || name.includes('nube');
            const isPickupKeyword = name.includes('sucursal') || name.includes('retiro') || name.includes('local');
            return isHomeKeyword && !isPickupKeyword;
        });
    }

    getOpcionesRetiro() {
        return this.shippingOptions.filter(o => {
            const name = o.nombre.toLowerCase();
            return name.includes('sucursal') || name.includes('retiro') || name.includes('local');
        });
    }

    getDiscountAmount() {
        const shipping = this.getSelectedShipping();
        const metodoPago = this.pagoForm.get('metodo')?.value;
        const subtotalConEnvio = this.total + (shipping ? shipping.costo : 0);

        if (['efectivo_local', 'transferencia', 'efectivo'].includes(metodoPago)) {
            return subtotalConEnvio * 0.15;
        }
        return 0;
    }

    getFinalTotal() {
        const shipping = this.getSelectedShipping();
        const metodoPago = this.pagoForm.get('metodo')?.value;
        let total = this.total + (shipping ? shipping.costo : 0);

        // Descuento del 15%
        if (['efectivo_local', 'transferencia', 'efectivo'].includes(metodoPago)) {
            return total * 0.85;
        }

        // Aplicar cupón si existe (si no se aplicó el de transferencia)
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
                this.cdr.detectChanges();
            },
            error: (err) => {
                this.couponError = err.error?.error || 'Error al validar el cupón';
                this.validatingCoupon = false;
                this.appliedCoupon = null;
                this.cdr.detectChanges();
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
            dni: datos.dni,

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

    getFormattedImageUrl(url: string | null | undefined): string {
        return this.apiService.getFormattedImageUrl(url);
    }
}
