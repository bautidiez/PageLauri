import { Routes } from '@angular/router';
import { HomeComponent } from './pages/home/home';
import { ProductosComponent } from './pages/productos/productos';
import { ProductoDetailComponent } from './pages/producto-detail/producto-detail';
import { CartComponent } from './pages/cart/cart';
import { CheckoutComponent } from './pages/checkout/checkout';
import { ContactoComponent } from './pages/contacto/contacto';
import { PoliticaCambioComponent } from './pages/politica-cambio/politica-cambio';
import { GuiaTallesComponent } from './pages/guia-talles/guia-talles';
import { EncargoEspecialComponent } from './pages/encargo-especial/encargo-especial';
import { LoginComponent } from './pages/admin/login/login';
import { DashboardComponent } from './pages/admin/dashboard/dashboard';
import { GestionComponent } from './pages/admin/gestion/gestion';
import { ProductosAdminComponent } from './pages/admin/productos-admin/productos-admin';
import { PedidosAdminComponent } from './pages/admin/pedidos-admin/pedidos-admin';
import { StockAdminComponent } from './pages/admin/stock-admin/stock-admin';
import { PromocionesAdminComponent } from './pages/admin/promociones-admin/promociones-admin';
import { CategoriasAdminComponent } from './pages/admin/categorias-admin/categorias-admin';
import { VentasExternasAdminComponent } from './pages/admin/ventas-externas-admin/ventas-externas-admin';

export const routes: Routes = [
  { path: '', component: HomeComponent },
  { path: 'productos', component: ProductosComponent },
  { path: 'productos/:id', component: ProductoDetailComponent },

  // Routes for slug-based categories (generic)
  { path: 'categoria/:slug', component: ProductosComponent },
  { path: 'categoria/:parent/:slug', component: ProductosComponent },
  { path: 'categoria/:grandparent/:parent/:slug', component: ProductosComponent },

  // Backward compatibility - numeric category IDs (keep for old links/bookmarks)
  { path: 'categoria/id/:id', component: ProductosComponent }, // Changed prefix to avoid collision or keep as is if IDs are numeric and slugs are string. 
  // Should check if we need regex matcher or just order. 
  // Slugs are strings, IDs are numbers. Angular router matches first match. 
  // If we have 'categoria/:slug', it will catch 'categoria/13' too. 
  // We handle this in component logic: if param is numeric -> ID, else -> slug.

  { path: 'carrito', component: CartComponent },
  { path: 'checkout', loadComponent: () => import('./pages/checkout-v2/checkout-v2').then(m => m.CheckoutV2Component) },
  { path: 'mis-pedidos', loadComponent: () => import('./pages/mis-pedidos/mis-pedidos').then(m => m.MisPedidosComponent) },
  { path: 'contacto', component: ContactoComponent },
  { path: 'encargo-especial', component: EncargoEspecialComponent },
  { path: 'politica-cambio', component: PoliticaCambioComponent },
  { path: 'guia-talles', component: GuiaTallesComponent },
  { path: 'registro', loadComponent: () => import('./pages/registro/registro').then(m => m.RegistroComponent) },
  { path: 'login', loadComponent: () => import('./pages/login-cliente/login-cliente').then(m => m.LoginClienteComponent) },
  { path: 'recuperar-password', loadComponent: () => import('./pages/password-recovery/request-reset/request-reset.component').then(m => m.RequestResetComponent) },
  { path: 'reset-password', loadComponent: () => import('./pages/password-recovery/reset-password/reset-password.component').then(m => m.ResetPasswordComponent) },
  { path: 'admin/login', component: LoginComponent },
  { path: 'admin', component: DashboardComponent },
  { path: 'admin/gestion', component: GestionComponent },
  { path: 'admin/productos', component: ProductosAdminComponent },
  { path: 'admin/pedidos', component: PedidosAdminComponent },
  { path: 'admin/stock', component: StockAdminComponent },
  { path: 'admin/promociones', component: PromocionesAdminComponent },
  { path: 'admin/categorias', component: CategoriasAdminComponent },
  { path: 'admin/ventas-externas', component: VentasExternasAdminComponent },
  { path: '**', redirectTo: '' }
];
