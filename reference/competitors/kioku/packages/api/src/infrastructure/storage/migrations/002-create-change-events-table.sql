-- Migration 002: Create change_events table for file watcher audit trail
-- Feature: File Watching (User Story 3)
-- Purpose: Track file system changes for real-time context updates

CREATE TABLE IF NOT EXISTS change_events (
  id TEXT PRIMARY KEY,             -- UUID v4
  event_type TEXT NOT NULL,        -- FileEventType enum
  file_path TEXT NOT NULL,
  old_path TEXT,                   -- For renames
  timestamp INTEGER NOT NULL,      -- Unix timestamp
  processed BOOLEAN NOT NULL DEFAULT 0,
  error TEXT,
  created_at INTEGER NOT NULL
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_change_events_timestamp ON change_events(timestamp);
CREATE INDEX IF NOT EXISTS idx_change_events_processed ON change_events(processed);
CREATE INDEX IF NOT EXISTS idx_change_events_file_path ON change_events(file_path);
