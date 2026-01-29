import { Injectable, Inject, PLATFORM_ID } from '@angular/core';
import { Meta, Title } from '@angular/platform-browser';
import { isPlatformBrowser } from '@angular/common';

export interface SeoData {
    title?: string;
    description?: string;
    keywords?: string;
    image?: string;
    url?: string;
    type?: string;
    author?: string;
}

export interface StructuredData {
    '@context': string;
    '@type': string;
    [key: string]: any;
}

@Injectable({
    providedIn: 'root'
})
export class SeoService {
    private isBrowser: boolean;

    constructor(
        private meta: Meta,
        private title: Title,
        @Inject(PLATFORM_ID) platformId: object
    ) {
        this.isBrowser = isPlatformBrowser(platformId);
    }

    updateMetaTags(seoData: SeoData) {
        // Update title
        if (seoData.title) {
            this.title.setTitle(`${seoData.title} | El Vestuario`);
        }

        // Update meta description
        if (seoData.description) {
            this.meta.updateTag({ name: 'description', content: seoData.description });
        }

        // Update keywords
        if (seoData.keywords) {
            this.meta.updateTag({ name: 'keywords', content: seoData.keywords });
        }

        // Update Open Graph tags
        if (seoData.title) {
            this.meta.updateTag({ property: 'og:title', content: seoData.title });
        }
        if (seoData.description) {
            this.meta.updateTag({ property: 'og:description', content: seoData.description });
        }
        if (seoData.image) {
            this.meta.updateTag({ property: 'og:image', content: seoData.image });
        }
        if (seoData.url) {
            this.meta.updateTag({ property: 'og:url', content: seoData.url });
        }
        if (seoData.type) {
            this.meta.updateTag({ property: 'og:type', content: seoData.type });
        }

        // Update Twitter Card tags
        this.meta.updateTag({ name: 'twitter:card', content: 'summary_large_image' });
        if (seoData.title) {
            this.meta.updateTag({ name: 'twitter:title', content: seoData.title });
        }
        if (seoData.description) {
            this.meta.updateTag({ name: 'twitter:description', content: seoData.description });
        }
        if (seoData.image) {
            this.meta.updateTag({ name: 'twitter:image', content: seoData.image });
        }

        // Update author
        if (seoData.author) {
            this.meta.updateTag({ name: 'author', content: seoData.author });
        }
    }

    addStructuredData(data: StructuredData) {
        if (!this.isBrowser) return;

        const scriptId = `structured-data-${data['@type']}`;

        // Remove existing script if present
        const existingScript = document.getElementById(scriptId);
        if (existingScript) {
            existingScript.remove();
        }

        // Create new script tag
        const script = document.createElement('script');
        script.id = scriptId;
        script.type = 'application/ld+json';
        script.text = JSON.stringify(data);
        document.head.appendChild(script);
    }

    generateProductSchema(product: any): StructuredData {
        const schema: StructuredData = {
            '@context': 'https://schema.org',
            '@type': 'Product',
            'name': product.nombre,
            'description': product.descripcion || `${product.nombre} - El Vestuario`,
            'image': product.imagenes && product.imagenes.length > 0
                ? `https://elvestuario-backend.onrender.com${product.imagenes[0].url}`
                : '',
            'brand': {
                '@type': 'Brand',
                'name': 'El Vestuario'
            }
        };

        // Add price information
        if (product.precio_base) {
            schema['offers'] = {
                '@type': 'Offer',
                'priceCurrency': 'ARS',
                'price': product.precio_descuento || product.precio_base,
                'availability': product.tiene_stock
                    ? 'https://schema.org/InStock'
                    : 'https://schema.org/OutOfStock',
                'url': window.location.href
            };

            // Add discounted price if applicable
            if (product.precio_descuento && product.precio_descuento < product.precio_base) {
                schema['offers']['priceValidUntil'] = new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];
            }
        }

        // Add SKU if available
        if (product.id) {
            schema['sku'] = `PROD-${product.id}`;
        }

        return schema;
    }

    generateOrganizationSchema(): StructuredData {
        return {
            '@context': 'https://schema.org',
            '@type': 'Organization',
            'name': 'El Vestuario',
            'url': 'https://elvestuario-r4.com.ar',
            'logo': 'https://elvestuario-r4.com.ar/assets/logo.png',
            'contactPoint': {
                '@type': 'ContactPoint',
                'contactType': 'customer service',
                'availableLanguage': 'Spanish'
            },
            'sameAs': [
                // Add social media links here when available
            ]
        };
    }

    generateBreadcrumbSchema(items: Array<{ name: string; url: string }>): StructuredData {
        return {
            '@context': 'https://schema.org',
            '@type': 'BreadcrumbList',
            'itemListElement': items.map((item, index) => ({
                '@type': 'ListItem',
                'position': index + 1,
                'name': item.name,
                'item': item.url
            }))
        };
    }

    setCanonicalUrl(url: string) {
        if (!this.isBrowser) return;

        let link: HTMLLinkElement | null = document.querySelector('link[rel="canonical"]');

        if (!link) {
            link = document.createElement('link');
            link.setAttribute('rel', 'canonical');
            document.head.appendChild(link);
        }

        link.setAttribute('href', url);
    }

    removeStructuredData(type: string) {
        if (!this.isBrowser) return;

        const scriptId = `structured-data-${type}`;
        const script = document.getElementById(scriptId);
        if (script) {
            script.remove();
        }
    }
}
