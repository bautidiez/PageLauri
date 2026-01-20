-- SCRIPT SQL PARA CHECKOUT PROFESIONAL (POSTGRESQL)

-- 1. Usuarios / Clientes
CREATE TABLE IF NOT EXISTS customers (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(200) NOT NULL,
    email VARCHAR(200) UNIQUE NOT NULL,
    telefono VARCHAR(50),
    password_hash VARCHAR(255),
    acepta_newsletter BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. Direcciones
CREATE TABLE IF NOT EXISTS addresses (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER REFERENCES customers(id) ON DELETE CASCADE,
    calle VARCHAR(200) NOT NULL,
    altura VARCHAR(50) NOT NULL,
    piso VARCHAR(20),
    ciudad VARCHAR(200) NOT NULL,
    provincia VARCHAR(200) NOT NULL,
    codigo_postal VARCHAR(20) NOT NULL,
    es_predeterminada BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 3. Productos (Simplificado para este script, asumiendo tabla existente)
CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(200) NOT NULL,
    precio_base DECIMAL(10,2) NOT NULL,
    precio_descuento DECIMAL(10,2),
    activo BOOLEAN DEFAULT TRUE,
    stock INTEGER DEFAULT 0
);

-- 4. Pedidos (Orders)
CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    numero_pedido VARCHAR(50) UNIQUE NOT NULL,
    customer_id INTEGER REFERENCES customers(id),
    cliente_nombre VARCHAR(200) NOT NULL,
    cliente_email VARCHAR(200) NOT NULL,
    cliente_telefono VARCHAR(50),
    
    -- Dirección de entrega snapshot (para historiales)
    direccion_calle VARCHAR(200) NOT NULL,
    direccion_altura VARCHAR(50) NOT NULL,
    direccion_ciudad VARCHAR(200) NOT NULL,
    direccion_provincia VARCHAR(200) NOT NULL,
    direccion_cp VARCHAR(20) NOT NULL,
    
    subtotal DECIMAL(10,2) NOT NULL,
    descuento DECIMAL(10,2) DEFAULT 0,
    costo_envio DECIMAL(10,2) DEFAULT 0,
    total DECIMAL(10,2) NOT NULL,
    
    estado VARCHAR(50) DEFAULT 'pendiente', -- pendiente, pagado, preparando, enviado, entregado, cancelado
    metodo_pago VARCHAR(50), -- transferencia, mercadopago
    metodo_envio VARCHAR(100), -- correo_argentino, andreani, retiro
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 5. Items del Pedido
CREATE TABLE IF NOT EXISTS order_items (
    id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES orders(id) ON DELETE CASCADE,
    product_id INTEGER REFERENCES products(id),
    producto_nombre VARCHAR(200) NOT NULL,
    talle VARCHAR(50),
    cantidad INTEGER NOT NULL,
    precio_unitario DECIMAL(10,2) NOT NULL,
    subtotal DECIMAL(10,2) NOT NULL
);

-- 6. Pagos
CREATE TABLE IF NOT EXISTS payments (
    id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES orders(id) ON DELETE CASCADE,
    metodo VARCHAR(50) NOT NULL,
    estado VARCHAR(50) DEFAULT 'pendiente', -- pendiente, aprobado, rechazado
    external_id VARCHAR(100), -- ID de Mercado Pago
    comprobante_url VARCHAR(500), -- Para transferencias
    codigo_pago_unico VARCHAR(50), -- Para transferencias
    monto_pagado DECIMAL(10,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 7. Envíos y Tracking
CREATE TABLE IF NOT EXISTS shipments (
    id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES orders(id) ON DELETE CASCADE,
    transportista VARCHAR(100) NOT NULL,
    numero_guia VARCHAR(100),
    estado VARCHAR(50) DEFAULT 'preparando',
    costo DECIMAL(10,2),
    tiempo_estimado VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 8. Historial de Seguimiento
CREATE TABLE IF NOT EXISTS tracking_updates (
    id SERIAL PRIMARY KEY,
    shipment_id INTEGER REFERENCES shipments(id) ON DELETE CASCADE,
    estado VARCHAR(50) NOT NULL,
    descripcion TEXT,
    fecha TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Índices para optimización
CREATE INDEX idx_orders_customer ON orders(customer_id);
CREATE INDEX idx_orders_email ON orders(cliente_email);
CREATE INDEX idx_orders_numero ON orders(numero_pedido);
CREATE INDEX idx_order_items_order ON order_items(order_id);
CREATE INDEX idx_payments_order ON payments(order_id);
CREATE INDEX idx_shipments_order ON shipments(order_id);
