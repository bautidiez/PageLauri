-- Script para eliminar la talla XS del sistema
-- Ejecutar esto en el panel de PostgreSQL de Render

DELETE FROM stock_talles WHERE talle_id IN (SELECT id FROM talles WHERE nombre = 'XS');
DELETE FROM talles WHERE nombre = 'XS';

-- Opcional: Verificar que solo quedan talles S, M, L, XL, XXL
SELECT * FROM talles ORDER BY orden;
