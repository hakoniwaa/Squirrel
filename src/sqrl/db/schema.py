"""
SQLite schema for Squirrel memory system.

Implements:
- SCHEMA-001: memories
- SCHEMA-002: evidence
- SCHEMA-003: memory_metrics
- SCHEMA-004: episodes
"""

import sqlite3
from pathlib import Path
from typing import Optional

# Schema version for migrations
SCHEMA_VERSION = 1

SCHEMA_SQL = """
-- SCHEMA-001: memories
CREATE TABLE IF NOT EXISTS memories (
    id          TEXT PRIMARY KEY,
    project_id  TEXT,
    scope       TEXT NOT NULL CHECK (scope IN ('global', 'project', 'repo_path')),

    owner_type  TEXT NOT NULL CHECK (owner_type IN ('user', 'team', 'org')),
    owner_id    TEXT NOT NULL,

    kind        TEXT NOT NULL CHECK (kind IN ('preference', 'invariant', 'pattern', 'guard', 'note')),
    tier        TEXT NOT NULL CHECK (tier IN ('short_term', 'long_term', 'emergency')),
    polarity    INTEGER DEFAULT 1 CHECK (polarity IN (1, -1)),
    key         TEXT,
    text        TEXT NOT NULL,

    status      TEXT NOT NULL DEFAULT 'provisional' CHECK (status IN ('provisional', 'active', 'deprecated')),
    confidence  REAL CHECK (confidence >= 0.0 AND confidence <= 1.0),
    expires_at  TEXT,
    embedding   BLOB,

    created_at  TEXT NOT NULL,
    updated_at  TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_memories_project ON memories(project_id);
CREATE INDEX IF NOT EXISTS idx_memories_scope ON memories(scope);
CREATE INDEX IF NOT EXISTS idx_memories_owner ON memories(owner_type, owner_id);
CREATE INDEX IF NOT EXISTS idx_memories_kind ON memories(kind);
CREATE INDEX IF NOT EXISTS idx_memories_tier ON memories(tier);
CREATE INDEX IF NOT EXISTS idx_memories_key ON memories(key);
CREATE INDEX IF NOT EXISTS idx_memories_status ON memories(status);

-- SCHEMA-002: evidence
CREATE TABLE IF NOT EXISTS evidence (
    id           TEXT PRIMARY KEY,
    memory_id    TEXT NOT NULL,
    episode_id   TEXT NOT NULL,
    source       TEXT CHECK (source IN ('failure_then_success', 'user_correction', 'explicit_statement', 'pattern_observed', 'guard_triggered')),
    frustration  TEXT CHECK (frustration IN ('none', 'mild', 'moderate', 'severe')),
    created_at   TEXT NOT NULL,
    FOREIGN KEY (memory_id) REFERENCES memories(id),
    FOREIGN KEY (episode_id) REFERENCES episodes(id)
);

CREATE INDEX IF NOT EXISTS idx_evidence_memory ON evidence(memory_id);
CREATE INDEX IF NOT EXISTS idx_evidence_episode ON evidence(episode_id);

-- SCHEMA-003: memory_metrics
CREATE TABLE IF NOT EXISTS memory_metrics (
    memory_id              TEXT PRIMARY KEY,
    use_count              INTEGER DEFAULT 0,
    opportunities          INTEGER DEFAULT 0,
    suspected_regret_hits  INTEGER DEFAULT 0,
    estimated_regret_saved REAL DEFAULT 0.0,
    last_used_at           TEXT,
    last_evaluated_at      TEXT,
    FOREIGN KEY (memory_id) REFERENCES memories(id)
);

-- SCHEMA-004: episodes
CREATE TABLE IF NOT EXISTS episodes (
    id          TEXT PRIMARY KEY,
    project_id  TEXT NOT NULL,
    start_ts    TEXT NOT NULL,
    end_ts      TEXT NOT NULL,
    events_json TEXT NOT NULL,
    processed   INTEGER DEFAULT 0,
    created_at  TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_episodes_project ON episodes(project_id);
CREATE INDEX IF NOT EXISTS idx_episodes_processed ON episodes(processed);
CREATE INDEX IF NOT EXISTS idx_episodes_start ON episodes(start_ts);

-- Schema version tracking
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY
);
"""


def get_db_path(project_path: Optional[Path] = None) -> Path:
    """
    Get database path based on scope.

    - Global: ~/.sqrl/squirrel.db
    - Project: <project>/.sqrl/squirrel.db
    """
    if project_path:
        db_dir = project_path / ".sqrl"
    else:
        db_dir = Path.home() / ".sqrl"

    db_dir.mkdir(parents=True, exist_ok=True)
    return db_dir / "squirrel.db"


def get_connection(db_path: Optional[Path] = None) -> sqlite3.Connection:
    """Get a database connection with proper settings."""
    if db_path is None:
        db_path = get_db_path()

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def init_db(db_path: Optional[Path] = None) -> sqlite3.Connection:
    """Initialize database with schema."""
    conn = get_connection(db_path)

    # Check if already initialized
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='schema_version'"
    )
    if cursor.fetchone():
        # Already initialized, check version
        cursor = conn.execute("SELECT version FROM schema_version LIMIT 1")
        row = cursor.fetchone()
        if row and row[0] >= SCHEMA_VERSION:
            return conn

    # Initialize schema
    conn.executescript(SCHEMA_SQL)
    conn.execute(
        "INSERT OR REPLACE INTO schema_version (version) VALUES (?)",
        (SCHEMA_VERSION,)
    )
    conn.commit()

    return conn
