-- Migration: Add user settings and profile columns
-- Date: 2025-12-23
-- Description: Adds settings, preferences, profile fields, and updated_at to users table

-- Add new columns to users table
ALTER TABLE users
ADD COLUMN IF NOT EXISTS settings JSONB DEFAULT '{}'::jsonb,
ADD COLUMN IF NOT EXISTS preferences JSONB DEFAULT '{}'::jsonb,
ADD COLUMN IF NOT EXISTS avatar_url TEXT,
ADD COLUMN IF NOT EXISTS bio TEXT,
ADD COLUMN IF NOT EXISTS organization TEXT,
ADD COLUMN IF NOT EXISTS timezone TEXT DEFAULT 'UTC',
ADD COLUMN IF NOT EXISTS language TEXT DEFAULT 'en',
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT NOW();

-- Create indexes for commonly queried fields
CREATE INDEX IF NOT EXISTS idx_users_updated_at ON users(updated_at);

-- Add comment for documentation
COMMENT ON COLUMN users.settings IS 'User UI/UX settings (theme, notifications, etc.)';
COMMENT ON COLUMN users.preferences IS 'User preferences (default model, etc.)';
COMMENT ON COLUMN users.avatar_url IS 'URL to user avatar image';
COMMENT ON COLUMN users.bio IS 'User biography/description';
COMMENT ON COLUMN users.organization IS 'User organization/institution';
COMMENT ON COLUMN users.timezone IS 'User timezone (default: UTC)';
COMMENT ON COLUMN users.language IS 'User preferred language (default: en)';

-- Update existing users to have default values
UPDATE users 
SET 
    settings = '{}'::jsonb,
    preferences = '{}'::jsonb,
    timezone = 'UTC',
    language = 'en',
    updated_at = NOW()
WHERE settings IS NULL OR preferences IS NULL;
