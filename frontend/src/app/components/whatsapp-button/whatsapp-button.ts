import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-whatsapp-button',
  imports: [CommonModule],
  templateUrl: './whatsapp-button.html',
  styleUrl: './whatsapp-button.css'
})
export class WhatsAppButtonComponent {
  whatsappNumber = '5493585164402';
  whatsappMessage = 'Hola! Me gustaría hacer una consulta sobre sus productos.';

  openWhatsApp() {
    const url = `https://wa.me/${this.whatsappNumber}?text=${encodeURIComponent(this.whatsappMessage)}`;
    window.open(url, '_blank');
  }
}
