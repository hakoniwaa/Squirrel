//! SQLite storage for memories and doc debt.
//!
//! SCHEMA-001: memories in <repo>/.sqrl/memory.db
//! SCHEMA-002: doc_debt in <repo>/.sqrl/memory.db

use std::fs;
use std::path::{Path, PathBuf};

use rusqlite::{Connection, Result as SqliteResult};
use serde::{Deserialize, Serialize};

use crate::error::Error;

// === Database Path ===

/// Get the project database path.
fn db_path(project_root: &Path) -> PathBuf {
    project_root.join(".sqrl").join("memory.db")
}

// === Memory (SCHEMA-001) ===

/// A stored memory.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Memory {
    pub id: String,
    pub memory_type: String,
    pub content: String,
    pub tags: Vec<String>,
    pub use_count: i64,
    pub created_at: String,
    pub updated_at: String,
}

/// Ensure the memories table exists.
fn ensure_memories_table(conn: &Connection) -> SqliteResult<()> {
    conn.execute(
        "CREATE TABLE IF NOT EXISTS memories (
            id           TEXT PRIMARY KEY,
            memory_type  TEXT NOT NULL,
            content      TEXT NOT NULL,
            tags         TEXT DEFAULT '[]',
            use_count    INTEGER DEFAULT 1,
            created_at   TEXT NOT NULL,
            updated_at   TEXT NOT NULL
        )",
        [],
    )?;
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_memories_type ON memories(memory_type)",
        [],
    )?;
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_memories_use_count ON memories(use_count DESC)",
        [],
    )?;
    Ok(())
}

/// Store a memory. Deduplicates by content (increments use_count if exists).
pub fn store_memory(
    project_root: &Path,
    memory_type: &str,
    content: &str,
    tags: &[String],
) -> Result<(String, bool, i64), Error> {
    let path = db_path(project_root);
    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent)?;
    }

    let conn = Connection::open(&path)?;
    ensure_memories_table(&conn)?;

    // Check for existing memory with same content
    let existing: Option<(String, i64)> = conn
        .query_row(
            "SELECT id, use_count FROM memories WHERE content = ?1",
            [content],
            |row| Ok((row.get(0)?, row.get(1)?)),
        )
        .ok();

    if let Some((id, use_count)) = existing {
        let new_count = use_count + 1;
        let now = chrono::Utc::now().to_rfc3339();
        conn.execute(
            "UPDATE memories SET use_count = ?1, updated_at = ?2 WHERE id = ?3",
            rusqlite::params![new_count, now, id],
        )?;
        Ok((id, true, new_count))
    } else {
        let id = uuid::Uuid::new_v4().to_string();
        let now = chrono::Utc::now().to_rfc3339();
        let tags_json = serde_json::to_string(tags)?;

        conn.execute(
            "INSERT INTO memories (id, memory_type, content, tags, use_count, created_at, updated_at)
             VALUES (?1, ?2, ?3, ?4, 1, ?5, ?6)",
            rusqlite::params![id, memory_type, content, tags_json, now, now],
        )?;
        Ok((id, false, 1))
    }
}

/// Get memories, optionally filtered by type and/or tags.
pub fn get_memories(
    project_root: &Path,
    memory_type: Option<&str>,
    tags: Option<&[String]>,
    limit: Option<i64>,
) -> Result<Vec<Memory>, Error> {
    let path = db_path(project_root);
    if !path.exists() {
        return Ok(vec![]);
    }

    let conn = Connection::open(&path)?;

    // Check if table exists
    let table_exists: i32 = conn.query_row(
        "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='memories'",
        [],
        |row| row.get(0),
    )?;
    if table_exists == 0 {
        return Ok(vec![]);
    }

    let mut sql = String::from(
        "SELECT id, memory_type, content, tags, use_count, created_at, updated_at FROM memories",
    );
    let mut conditions = Vec::new();

    if memory_type.is_some() {
        conditions.push("memory_type = ?1".to_string());
    }

    if !conditions.is_empty() {
        sql.push_str(" WHERE ");
        sql.push_str(&conditions.join(" AND "));
    }

    sql.push_str(" ORDER BY use_count DESC");

    if let Some(lim) = limit {
        sql.push_str(&format!(" LIMIT {}", lim));
    }

    let mut stmt = conn.prepare(&sql)?;

    let row_mapper = |row: &rusqlite::Row| {
        let tags_json: String = row.get(3)?;
        Ok(Memory {
            id: row.get(0)?,
            memory_type: row.get(1)?,
            content: row.get(2)?,
            tags: serde_json::from_str(&tags_json).unwrap_or_default(),
            use_count: row.get(4)?,
            created_at: row.get(5)?,
            updated_at: row.get(6)?,
        })
    };

    let mut memories = Vec::new();
    if let Some(mt) = memory_type {
        let rows = stmt.query_map([mt], row_mapper)?;
        for row in rows {
            memories.push(row?);
        }
    } else {
        let rows = stmt.query_map([], row_mapper)?;
        for row in rows {
            memories.push(row?);
        }
    };

    // Filter by tags if specified (post-query since SQLite JSON is limited)
    if let Some(filter_tags) = tags {
        if !filter_tags.is_empty() {
            memories.retain(|m| filter_tags.iter().any(|t| m.tags.contains(t)));
        }
    }

    Ok(memories)
}

/// Format memories as markdown grouped by type (for MCP response).
pub fn format_memories_as_markdown(
    project_root: &Path,
    memory_type: Option<&str>,
    tags: Option<&[String]>,
    limit: Option<i64>,
) -> Result<String, Error> {
    let memories = get_memories(project_root, memory_type, tags, limit)?;

    if memories.is_empty() {
        return Ok("No memories found.".to_string());
    }

    // Group by type
    let mut grouped: std::collections::BTreeMap<String, Vec<&Memory>> =
        std::collections::BTreeMap::new();
    for memory in &memories {
        grouped
            .entry(memory.memory_type.clone())
            .or_default()
            .push(memory);
    }

    let mut output = String::new();
    for (mtype, mems) in &grouped {
        output.push_str(&format!("## {} ({})\n", mtype, mems.len()));
        for m in mems {
            output.push_str(&format!("- [used {}x] {}\n", m.use_count, m.content));
        }
        output.push('\n');
    }

    Ok(output.trim_end().to_string())
}

/// Get memory count by type.
pub fn get_memory_counts(
    project_root: &Path,
) -> Result<std::collections::HashMap<String, i64>, Error> {
    let path = db_path(project_root);
    if !path.exists() {
        return Ok(std::collections::HashMap::new());
    }

    let conn = Connection::open(&path)?;

    let table_exists: i32 = conn.query_row(
        "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='memories'",
        [],
        |row| row.get(0),
    )?;
    if table_exists == 0 {
        return Ok(std::collections::HashMap::new());
    }

    let mut stmt =
        conn.prepare("SELECT memory_type, COUNT(*) FROM memories GROUP BY memory_type")?;
    let rows = stmt.query_map([], |row| {
        let mtype: String = row.get(0)?;
        let count: i64 = row.get(1)?;
        Ok((mtype, count))
    })?;

    let mut counts = std::collections::HashMap::new();
    for row in rows {
        let (mtype, count) = row?;
        counts.insert(mtype, count);
    }

    Ok(counts)
}

// === Doc Debt (SCHEMA-002) ===

/// Doc debt entry.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DocDebt {
    pub id: String,
    pub commit_sha: String,
    pub commit_message: Option<String>,
    pub code_files: Vec<String>,
    pub expected_docs: Vec<String>,
    pub detection_rule: String,
    pub resolved: bool,
    pub resolved_at: Option<String>,
    pub created_at: String,
}

/// Ensure doc_debt table exists.
fn ensure_doc_debt_table(conn: &Connection) -> SqliteResult<()> {
    conn.execute(
        "CREATE TABLE IF NOT EXISTS doc_debt (
            id              TEXT PRIMARY KEY,
            commit_sha      TEXT NOT NULL,
            commit_message  TEXT,
            code_files      TEXT NOT NULL,
            expected_docs   TEXT NOT NULL,
            detection_rule  TEXT NOT NULL,
            resolved        INTEGER DEFAULT 0,
            resolved_at     TEXT,
            created_at      TEXT NOT NULL
        )",
        [],
    )?;
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_doc_debt_commit ON doc_debt(commit_sha)",
        [],
    )?;
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_doc_debt_resolved ON doc_debt(resolved)",
        [],
    )?;
    Ok(())
}

/// Add a doc debt entry.
pub fn add_doc_debt(
    project_root: &Path,
    commit_sha: &str,
    commit_message: Option<&str>,
    code_files: &[String],
    expected_docs: &[String],
    detection_rule: &str,
) -> Result<String, Error> {
    let path = db_path(project_root);
    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent)?;
    }

    let conn = Connection::open(&path)?;
    ensure_doc_debt_table(&conn)?;

    let id = uuid::Uuid::new_v4().to_string();
    let code_files_json = serde_json::to_string(code_files)?;
    let expected_docs_json = serde_json::to_string(expected_docs)?;
    let created_at = chrono::Utc::now().to_rfc3339();

    conn.execute(
        "INSERT INTO doc_debt (id, commit_sha, commit_message, code_files, expected_docs, detection_rule, resolved, created_at)
         VALUES (?1, ?2, ?3, ?4, ?5, ?6, 0, ?7)",
        rusqlite::params![id, commit_sha, commit_message, code_files_json, expected_docs_json, detection_rule, created_at],
    )?;

    Ok(id)
}

/// Get unresolved doc debt.
pub fn get_unresolved_doc_debt(project_root: &Path) -> Result<Vec<DocDebt>, Error> {
    let path = db_path(project_root);
    if !path.exists() {
        return Ok(vec![]);
    }

    let conn = Connection::open(&path)?;

    let table_exists: i32 = conn.query_row(
        "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='doc_debt'",
        [],
        |row| row.get(0),
    )?;
    if table_exists == 0 {
        return Ok(vec![]);
    }

    let mut stmt = conn.prepare(
        "SELECT id, commit_sha, commit_message, code_files, expected_docs, detection_rule, resolved, resolved_at, created_at
         FROM doc_debt WHERE resolved = 0 ORDER BY created_at DESC",
    )?;

    let debts = stmt
        .query_map([], |row| {
            let code_files_json: String = row.get(3)?;
            let expected_docs_json: String = row.get(4)?;
            let resolved_int: i32 = row.get(6)?;

            Ok(DocDebt {
                id: row.get(0)?,
                commit_sha: row.get(1)?,
                commit_message: row.get(2)?,
                code_files: serde_json::from_str(&code_files_json).unwrap_or_default(),
                expected_docs: serde_json::from_str(&expected_docs_json).unwrap_or_default(),
                detection_rule: row.get(5)?,
                resolved: resolved_int != 0,
                resolved_at: row.get(7)?,
                created_at: row.get(8)?,
            })
        })?
        .collect::<SqliteResult<Vec<_>>>()?;

    Ok(debts)
}

/// Check if doc debt exists for a commit.
pub fn has_doc_debt_for_commit(project_root: &Path, commit_sha: &str) -> Result<bool, Error> {
    let path = db_path(project_root);
    if !path.exists() {
        return Ok(false);
    }

    let conn = Connection::open(&path)?;

    let table_exists: i32 = conn.query_row(
        "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='doc_debt'",
        [],
        |row| row.get(0),
    )?;
    if table_exists == 0 {
        return Ok(false);
    }

    let count: i32 = conn.query_row(
        "SELECT COUNT(*) FROM doc_debt WHERE commit_sha = ?1",
        [commit_sha],
        |row| row.get(0),
    )?;

    Ok(count > 0)
}

#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::tempdir;

    #[test]
    fn test_store_and_get_memory() {
        let dir = tempdir().unwrap();
        let sqrl_dir = dir.path().join(".sqrl");
        fs::create_dir_all(&sqrl_dir).unwrap();

        let (id, deduped, count) = store_memory(
            dir.path(),
            "preference",
            "No emojis",
            &["style".to_string()],
        )
        .unwrap();
        assert!(!deduped);
        assert_eq!(count, 1);
        assert!(!id.is_empty());

        // Store same memory again - should dedup
        let (id2, deduped2, count2) = store_memory(
            dir.path(),
            "preference",
            "No emojis",
            &["style".to_string()],
        )
        .unwrap();
        assert!(deduped2);
        assert_eq!(count2, 2);
        assert_eq!(id, id2);

        // Get memories
        let memories = get_memories(dir.path(), None, None, None).unwrap();
        assert_eq!(memories.len(), 1);
        assert_eq!(memories[0].use_count, 2);
    }

    #[test]
    fn test_get_memories_empty() {
        let dir = tempdir().unwrap();
        let result = get_memories(dir.path(), None, None, None);
        assert!(result.is_ok());
        assert!(result.unwrap().is_empty());
    }

    #[test]
    fn test_format_memories_empty() {
        let dir = tempdir().unwrap();
        let result = format_memories_as_markdown(dir.path(), None, None, None);
        assert!(result.is_ok());
        assert_eq!(result.unwrap(), "No memories found.");
    }
}
