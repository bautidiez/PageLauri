-- Migración: Agregar índices a la tabla stock_talles para optimizar consultas
-- Fecha: 2026-01-16
-- Descripción: Mejora el rendimiento de consultas en el módulo de Gestión de Stock

-- Crear índice en producto_id (para filtrar por producto)
CREATE INDEX IF NOT EXISTS idx_stock_producto ON stock_talles(producto_id);

-- Crear índice en talle_id (para filtrar por talle)
CREATE INDEX IF NOT EXISTS idx_stock_talle ON stock_talles(talle_id);

-- Crear índice en cantidad (para filtrar por stock bajo)
CREATE INDEX IF NOT EXISTS idx_stock_cantidad ON stock_talles(cantidad);

-- Crear índice compuesto en producto_id y cantidad (para consultas combinadas)
CREATE INDEX IF NOT EXISTS idx_stock_producto_cantidad ON stock_talles(producto_id, cantidad);

-- Verificar índices creados
SELECT 
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename = 'stock_talles'
ORDER BY indexname;
