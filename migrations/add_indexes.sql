-- Migration: Add database indexes for performance optimization
-- Date: 2024-12-22
-- HIGH-003: Missing Database Indexes

-- Add index on projects.user_id (foreign key lookup)
CREATE INDEX IF NOT EXISTS idx_projects_user_id ON projects(user_id);

-- Add index on conversations.project_id (foreign key lookup)
CREATE INDEX IF NOT EXISTS idx_conversations_project_id ON conversations(project_id);

-- Add index on conversations.updated_at (recent conversations query)
CREATE INDEX IF NOT EXISTS idx_conversations_updated_at ON conversations(updated_at DESC);

-- Add index on messages.conversation_id (foreign key lookup)
CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages(conversation_id);

-- Add index on messages.created_at (message ordering)
CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at);

-- Add index on documents.project_id (foreign key lookup)
CREATE INDEX IF NOT EXISTS idx_documents_project_id ON documents(project_id);

-- Performance: Composite index for common query patterns
-- Messages by conversation ordered by time (most common query)
CREATE INDEX IF NOT EXISTS idx_messages_conv_time ON messages(conversation_id, created_at);

-- Verify indexes were created
SELECT 
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE schemaname = 'public'
ORDER BY tablename, indexname;
