-- Migration 005: Extend sessions table with v2.0 columns
-- Feature: All v2.0 features
-- Purpose: Track additional session metrics (git usage, AI discoveries, file changes)

-- Add new columns to existing sessions table
ALTER TABLE sessions ADD COLUMN git_tools_used INTEGER DEFAULT 0;
ALTER TABLE sessions ADD COLUMN git_commits_queried TEXT;  -- JSON array of commit SHAs
ALTER TABLE sessions ADD COLUMN ai_discoveries_count INTEGER DEFAULT 0;
ALTER TABLE sessions ADD COLUMN files_watched_changed INTEGER DEFAULT 0;
