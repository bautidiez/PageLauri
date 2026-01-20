-- Migration: Add ventas_externas table for external sales tracking
-- Creates table with all necessary columns and indexes

CREATE TABLE IF NOT EXISTS ventas_externas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    producto_id INTEGER NOT NULL,
    talle_id INTEGER NOT NULL,
    cantidad INTEGER NOT NULL,
    precio_unitario REAL NOT NULL,
    ganancia_total REAL NOT NULL,
    fecha DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    admin_id INTEGER NOT NULL,
    notas TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (producto_id) REFERENCES productos (id),
    FOREIGN KEY (talle_id) REFERENCES talles (id),
    FOREIGN KEY (admin_id) REFERENCES admins (id)
);

CREATE INDEX IF NOT EXISTS idx_venta_externa_producto ON ventas_externas (producto_id);
CREATE INDEX IF NOT EXISTS idx_venta_externa_fecha ON ventas_externas (fecha);
CREATE INDEX IF NOT EXISTS idx_venta_externa_admin ON ventas_externas (admin_id);
CREATE INDEX IF NOT EXISTS idx_venta_externa_fecha_producto ON ventas_externas (fecha, producto_id);
