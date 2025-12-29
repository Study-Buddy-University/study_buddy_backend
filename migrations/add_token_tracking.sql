-- Migration: Add token tracking fields
-- Date: 2025-01-21

-- Add token_count to messages table
ALTER TABLE messages ADD COLUMN IF NOT EXISTS token_count INTEGER DEFAULT NULL;

-- Add total_tokens to conversations table
ALTER TABLE conversations ADD COLUMN IF NOT EXISTS total_tokens INTEGER DEFAULT 0;

-- Update existing conversations to set total_tokens to 0 if NULL
UPDATE conversations SET total_tokens = 0 WHERE total_tokens IS NULL;
