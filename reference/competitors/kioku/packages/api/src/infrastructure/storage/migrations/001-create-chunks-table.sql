-- Migration 001: Create chunks table for function/class-level code storage
-- Feature: Smart Chunking (User Story 2)
-- Purpose: Store code chunk metadata (embeddings stored in ChromaDB)

CREATE TABLE IF NOT EXISTS chunks (
  id TEXT PRIMARY KEY,             -- UUID v4
  file_path TEXT NOT NULL,
  type TEXT NOT NULL,              -- ChunkType enum value
  name TEXT NOT NULL,
  start_line INTEGER NOT NULL,
  end_line INTEGER NOT NULL,
  content_start_line INTEGER NOT NULL,
  content_end_line INTEGER NOT NULL,
  code TEXT NOT NULL,
  content_hash TEXT NOT NULL,      -- SHA-256 hash for change detection
  parent_chunk_id TEXT,            -- Foreign key to chunks.id
  nesting_level INTEGER NOT NULL DEFAULT 0,
  scope_path TEXT,                 -- JSON array as string
  signature TEXT,
  js_doc TEXT,
  is_exported BOOLEAN NOT NULL DEFAULT 0,
  is_async BOOLEAN NOT NULL DEFAULT 0,
  parameters TEXT,                 -- JSON array as string
  return_type TEXT,
  complexity INTEGER,
  embedding_id TEXT,               -- Reference to Chroma
  created_at INTEGER NOT NULL,     -- Unix timestamp
  updated_at INTEGER NOT NULL,     -- Unix timestamp

  FOREIGN KEY (parent_chunk_id) REFERENCES chunks(id) ON DELETE CASCADE
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_chunks_file_path ON chunks(file_path);
CREATE INDEX IF NOT EXISTS idx_chunks_type ON chunks(type);
CREATE INDEX IF NOT EXISTS idx_chunks_name ON chunks(name);
CREATE INDEX IF NOT EXISTS idx_chunks_parent ON chunks(parent_chunk_id);
CREATE INDEX IF NOT EXISTS idx_chunks_updated ON chunks(updated_at);
