-- Add tools column to projects table for storing enabled tool names
-- This will store an array of tool names as JSON: ["calculator", "web_search"]

ALTER TABLE projects 
ADD COLUMN IF NOT EXISTS tools JSONB DEFAULT '[]'::jsonb;

-- Add comment for documentation
COMMENT ON COLUMN projects.tools IS 'JSON array of enabled tool names for this project';
