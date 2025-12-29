-- Rollback Migration: Remove user settings and profile columns
-- Date: 2025-12-23
-- Description: Removes settings, preferences, and profile fields from users table

-- Drop indexes
DROP INDEX IF EXISTS idx_users_updated_at;

-- Remove columns from users table
ALTER TABLE users
DROP COLUMN IF EXISTS settings,
DROP COLUMN IF EXISTS preferences,
DROP COLUMN IF EXISTS avatar_url,
DROP COLUMN IF EXISTS bio,
DROP COLUMN IF EXISTS organization,
DROP COLUMN IF EXISTS timezone,
DROP COLUMN IF EXISTS language,
DROP COLUMN IF EXISTS updated_at;
