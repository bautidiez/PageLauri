-- Migration to add cliente_dni to pedidos table
ALTER TABLE pedidos ADD COLUMN cliente_dni VARCHAR(20);

