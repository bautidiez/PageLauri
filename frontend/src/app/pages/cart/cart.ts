import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { CartService, CartItem } from '../../services/cart.service';
import { ShippingCalculatorComponent } from '../../components/shipping-calculator/shipping-calculator';

@Component({
  selector: 'app-cart',
  standalone: true,
  imports: [CommonModule, RouterModule, ShippingCalculatorComponent],
  templateUrl: './cart.html',
  styleUrl: './cart.css'
})
export class CartComponent implements OnInit {
  items: CartItem[] = [];
  total = 0;

  constructor(private cartService: CartService) { }

  ngOnInit() {
    this.cartService.cart$.subscribe(items => {
      this.items = items;
      this.total = this.cartService.getTotal();
    });
  }

  removeItem(index: number) {
    this.cartService.removeItem(index);
  }

  updateQuantity(index: number, cantidad: number) {
    if (cantidad > 0) {
      this.cartService.updateQuantity(index, cantidad);
    }
  }

  getSubtotal(): number {
    return this.items.reduce((sum, item) => {
      return sum + (item.precio_unitario * item.cantidad);
    }, 0);
  }

  getDescuentoTotal(): number {
    return this.items.reduce((sum, item) => {
      return sum + (item.descuento || 0);
    }, 0);
  }
}
