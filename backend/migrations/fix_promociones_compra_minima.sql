-- Add missing compra_minima column to promociones_productos table
ALTER TABLE promociones_productos 
ADD COLUMN IF NOT EXISTS compra_minima NUMERIC DEFAULT 0.0;

-- Update existing records to have a default value
UPDATE promociones_productos 
SET compra_minima = 0.0 
WHERE compra_minima IS NULL;
