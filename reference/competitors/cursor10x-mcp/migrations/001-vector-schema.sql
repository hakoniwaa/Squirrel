-- Vector functionality migration
-- This creates or updates the vectors table for storing embeddings

-- Create vectors table with F32_BLOB support
CREATE TABLE IF NOT EXISTS vectors (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  content_id INTEGER NOT NULL,
  content_type TEXT NOT NULL,
  vector F32_BLOB(128) NOT NULL,
  created_at INTEGER NOT NULL,
  metadata TEXT
);

-- Create indexes for optimized lookup
CREATE INDEX IF NOT EXISTS idx_vectors_content ON vectors(content_id, content_type);
CREATE INDEX IF NOT EXISTS idx_vectors_created_at ON vectors(created_at);

-- Create ANN index for vector similarity search if supported
CREATE INDEX IF NOT EXISTS idx_vectors_ann ON vectors(libsql_vector_idx(vector)) WHERE vector IS NOT NULL; 