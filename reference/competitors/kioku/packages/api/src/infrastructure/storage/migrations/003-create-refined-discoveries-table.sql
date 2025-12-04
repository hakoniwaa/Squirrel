-- Migration 003: Create refined_discoveries table for AI-enhanced discoveries
-- Feature: AI Discovery (User Story 4)
-- Purpose: Store discoveries refined by Claude API

CREATE TABLE IF NOT EXISTS refined_discoveries (
  id TEXT PRIMARY KEY,             -- UUID v4
  session_id TEXT NOT NULL,
  raw_content TEXT NOT NULL,
  refined_content TEXT NOT NULL,
  type TEXT NOT NULL,              -- DiscoveryType enum
  confidence REAL NOT NULL,        -- 0.0 to 1.0
  supporting_evidence TEXT NOT NULL,
  suggested_module TEXT,
  ai_model TEXT NOT NULL,
  tokens_used INTEGER NOT NULL,
  processing_time INTEGER NOT NULL,  -- Milliseconds
  accepted BOOLEAN NOT NULL DEFAULT 0,
  applied_at INTEGER,              -- Unix timestamp
  created_at INTEGER NOT NULL,
  updated_at INTEGER NOT NULL,

  FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_refined_discoveries_session ON refined_discoveries(session_id);
CREATE INDEX IF NOT EXISTS idx_refined_discoveries_confidence ON refined_discoveries(confidence);
CREATE INDEX IF NOT EXISTS idx_refined_discoveries_accepted ON refined_discoveries(accepted);
CREATE INDEX IF NOT EXISTS idx_refined_discoveries_created ON refined_discoveries(created_at);
