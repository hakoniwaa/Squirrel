-- Migration 004: Create linked_projects and cross_references tables
-- Feature: Multi-Project (User Story 6)
-- Purpose: Store multi-project workspace links and cross-references

CREATE TABLE IF NOT EXISTS linked_projects (
  name TEXT PRIMARY KEY,
  path TEXT NOT NULL UNIQUE,
  link_type TEXT NOT NULL,         -- LinkType enum
  status TEXT NOT NULL,            -- ProjectStatus enum
  last_accessed INTEGER NOT NULL,  -- Unix timestamp
  tech_stack TEXT,                 -- JSON array as string
  module_count INTEGER,
  file_count INTEGER,
  created_at INTEGER NOT NULL,
  updated_at INTEGER NOT NULL
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_linked_projects_status ON linked_projects(status);
CREATE INDEX IF NOT EXISTS idx_linked_projects_last_accessed ON linked_projects(last_accessed);

CREATE TABLE IF NOT EXISTS cross_references (
  id TEXT PRIMARY KEY,             -- UUID v4
  source_project TEXT NOT NULL,
  source_file TEXT NOT NULL,
  target_project TEXT NOT NULL,
  target_file TEXT NOT NULL,
  reference_type TEXT NOT NULL,    -- 'import' | 'api_call' | 'type_usage'
  confidence REAL NOT NULL,        -- 0.0 to 1.0
  created_at INTEGER NOT NULL,

  FOREIGN KEY (source_project) REFERENCES linked_projects(name) ON DELETE CASCADE,
  FOREIGN KEY (target_project) REFERENCES linked_projects(name) ON DELETE CASCADE
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_cross_refs_source ON cross_references(source_project, source_file);
CREATE INDEX IF NOT EXISTS idx_cross_refs_target ON cross_references(target_project, target_file);
