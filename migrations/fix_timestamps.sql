-- Fix missing default values for timestamp columns
ALTER TABLE projects ALTER COLUMN created_at SET DEFAULT now();
ALTER TABLE projects ALTER COLUMN updated_at SET DEFAULT now();
