-- Add agent_name column to projects table
ALTER TABLE projects ADD COLUMN IF NOT EXISTS agent_name VARCHAR(100);
