import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-color-picker',
  imports: [CommonModule],
  templateUrl: './color-picker.component.html',
  styleUrl: './color-picker.component.css'
})
export class ColorPickerComponent {
  @Input() selectedColor: string = '';
  @Output() colorSelected = new EventEmitter<string>();

  // Colores predefinidos comunes
  colors = [
    { name: 'Rojo', hex: '#FF0000' },
    { name: 'Azul', hex: '#0000FF' },
    { name: 'Verde', hex: '#00FF00' },
    { name: 'Amarillo', hex: '#FFFF00' },
    { name: 'Naranja', hex: '#FFA500' },
    { name: 'Rosa', hex: '#FFC0CB' },
    { name: 'Morado', hex: '#800080' },
    { name: 'Negro', hex: '#000000' },
    { name: 'Blanco', hex: '#FFFFFF' },
    { name: 'Gris', hex: '#808080' },
    { name: 'Marrón', hex: '#A52A2A' },
    { name: 'Dorado', hex: '#FFD700' },
    { name: 'Plateado', hex: '#C0C0C0' },
    { name: 'Turquesa', hex: '#40E0D0' },
    { name: 'Verde Lima', hex: '#32CD32' },
    { name: 'Azul Marino', hex: '#000080' },
    { name: 'Rojo Oscuro', hex: '#8B0000' },
    { name: 'Verde Oscuro', hex: '#006400' },
    { name: 'Azul Cielo', hex: '#87CEEB' },
    { name: 'Coral', hex: '#FF7F50' }
  ];

  selectColor(color: any) {
    this.selectedColor = color.hex;
    this.colorSelected.emit(color);
  }

  getColorName(hex: string): string {
    const color = this.colors.find(c => c.hex === hex);
    return color ? color.name : '';
  }
}
