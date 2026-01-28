import { Component, EventEmitter, Output, ChangeDetectorRef, NgZone, Input, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Subject, of } from 'rxjs';
import { debounceTime, distinctUntilChanged, switchMap } from 'rxjs/operators';
import { ApiService } from '../../../services/api.service';

@Component({
  selector: 'app-add-stock-form',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="add-stock-form">
      <!-- PRODUCT SEARCH -->
      <div class="product-search-container">
        <label>Buscar Producto</label>
        <input
          type="text"
          class="form-control"
          [(ngModel)]="searchQuery"
          (input)="onSearchInput($event)"
          placeholder="Escribe para buscar..."
          [disabled]="selectedProduct !== null"
          autocomplete="off"
        />
        
        <!-- SEARCH RESULTS DROPDOWN -->
        <div class="search-results" *ngIf="searchResults.length > 0 && !selectedProduct">
          <div
            class="search-result-item"
            *ngFor="let product of searchResults"
            (click)="selectProduct(product)"
          >
            {{ product.nombre }}
          </div>
        </div>
        
        <!-- SEARCHING INDICATOR -->
        <div class="search-results" *ngIf="searching">
          <div class="search-result-item">Buscando...</div>
        </div>
      </div>

      <!-- SELECTED PRODUCT INFO -->
      <div class="selected-product-info" *ngIf="selectedProduct">
        <h4>{{ selectedProduct.nombre }}</h4>
        <button type="button" class="btn btn-secondary" (click)="clearSelection()" style="margin-top: 0.5rem; padding: 0.4rem 0.8rem; font-size: 0.85rem;">
          Cambiar producto
        </button>
      </div>

      <!-- SIZE INPUTS (S, M, L, XL, XXL) -->
      <div *ngIf="selectedProduct">
        <label style="display: block; margin-bottom: 0.75rem; font-weight: 600;">
          Agregar Stock por Talle (incrementa el stock actual)
        </label>
        <div class="sizes-grid">
          <div class="size-input-group" *ngFor="let size of sizes">
            <label>{{ size }}</label>
            <input
              type="number"
              [(ngModel)]="sizeInputs[size]"
              min="0"
              placeholder="0"
            />
          </div>
        </div>
      </div>

      <!-- FORM ACTIONS -->
      <div class="form-actions">
        <button
          type="button"
          class="btn btn-success"
          (click)="submitStock()"
          [disabled]="!selectedProduct || submitting"
        >
          {{ submitting ? 'Guardando...' : '💾 Guardar' }}
        </button>
        <button
          type="button"
          class="btn btn-secondary"
          (click)="cancel()"
          [disabled]="submitting"
        >
          Cancelar
        </button>
      </div>
    </div>
  `
})
export class AddStockFormComponent implements OnInit {
  @Input() preSelectedProduct: any = null;
  @Output() stockAdded = new EventEmitter<void>();
  @Output() cancelled = new EventEmitter<void>();

  selectedProduct: any = null;
  searchQuery = '';
  searchResults: any[] = [];
  searching = false;
  submitting = false;

  sizes = ['S', 'M', 'L', 'XL', 'XXL'];
  sizeInputs: { [key: string]: number } = {
    S: 0,
    M: 0,
    L: 0,
    XL: 0,
    XXL: 0
  };

  private searchSubject = new Subject<string>();

  ngOnInit() {
    if (this.preSelectedProduct) {
      this.selectProduct(this.preSelectedProduct);
    }
  }

  constructor(
    private apiService: ApiService,
    private cdr: ChangeDetectorRef,
    private zone: NgZone
  ) {
    // Setup debounced search
    this.searchSubject.pipe(
      debounceTime(300),
      distinctUntilChanged(),
      switchMap(query => {
        if (query.length < 2) {
          return of([]);
        }
        this.zone.run(() => {
          this.searching = true;
          this.cdr.detectChanges();
        });
        return this.apiService.searchProducts(query);
      })
    ).subscribe({
      next: (results) => {
        this.zone.run(() => {
          this.searchResults = results;
          this.searching = false;
          this.cdr.detectChanges(); // Force UI update with results
        });
      },
      error: (error) => {
        console.error('Error searching products:', error);
        this.zone.run(() => {
          this.searching = false;
          this.searchResults = [];
          this.cdr.detectChanges();
        });
      }
    });
  }

  onSearchInput(event: Event) {
    const value = (event.target as HTMLInputElement).value;
    this.searchQuery = value;
    this.searchSubject.next(value);
  }

  selectProduct(product: any) {
    this.selectedProduct = product;
    this.searchQuery = product.nombre;
    this.searchResults = [];

    // Reset size inputs
    this.sizes.forEach(size => {
      this.sizeInputs[size] = 0;
    });
  }

  clearSelection() {
    this.selectedProduct = null;
    this.searchQuery = '';
    this.searchResults = [];
  }

  submitStock() {
    if (!this.selectedProduct) {
      alert('Por favor selecciona un producto');
      return;
    }

    // Filter out zero values
    const increments: any = {};
    this.sizes.forEach(size => {
      if (this.sizeInputs[size] > 0) {
        increments[size] = this.sizeInputs[size];
      }
    });

    if (Object.keys(increments).length === 0) {
      alert('Por favor ingresa al menos una cantidad mayor a 0');
      return;
    }

    this.submitting = true;
    this.apiService.addStockBySizes(this.selectedProduct.id, increments).subscribe({
      next: (response) => {
        alert(`Stock agregado exitosamente para ${Object.keys(increments).length} talles`);
        this.stockAdded.emit();
      },
      error: (error) => {
        console.error('Error adding stock:', error);
        alert('Error al agregar stock. Por favor intenta nuevamente.');
        this.submitting = false;
      }
    });
  }

  cancel() {
    this.cancelled.emit();
  }
}
