//! SQLite storage for reading memories.
//!
//! SCHEMA-001: user_styles in ~/.sqrl/user_style.db
//! SCHEMA-002: project_memories in <repo>/.sqrl/memory.db
//! SCHEMA-006: doc_debt in <repo>/.sqrl/memory.db

use std::fs;
use std::path::{Path, PathBuf};

use chrono;
use rusqlite::{Connection, Result as SqliteResult};
use serde::{Deserialize, Serialize};
use serde_json;

use crate::error::Error;

// === User API Config ===

/// User API configuration.
#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct UserApiConfig {
    #[serde(default)]
    pub openrouter_api_key: Option<String>,
    #[serde(default)]
    pub model: Option<String>,
}

/// Get user config path.
fn user_config_path() -> Result<PathBuf, Error> {
    let home = dirs::home_dir().ok_or(Error::HomeDirNotFound)?;
    Ok(home.join(".sqrl").join("api_config.yaml"))
}

/// Load user API config.
pub fn get_user_api_config() -> Result<UserApiConfig, Error> {
    let path = user_config_path()?;
    if !path.exists() {
        return Ok(UserApiConfig::default());
    }
    let content = fs::read_to_string(&path)?;
    let config: UserApiConfig =
        serde_yaml::from_str(&content).map_err(|e| Error::ConfigParse(e.to_string()))?;
    Ok(config)
}

/// Save user API config.
pub fn save_user_api_config(config: &UserApiConfig) -> Result<(), Error> {
    let path = user_config_path()?;

    // Ensure directory exists
    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent)?;
    }

    let content = serde_yaml::to_string(config).map_err(|e| Error::ConfigParse(e.to_string()))?;
    let with_header = format!(
        "# Squirrel API configuration\n# Do not share this file - it contains sensitive keys\n\n{}",
        content
    );
    fs::write(&path, with_header)?;
    Ok(())
}

/// User style preference.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct UserStyle {
    pub id: String,
    pub text: String,
    pub use_count: i64,
}

/// Project-specific memory.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ProjectMemory {
    pub id: String,
    pub category: String,
    pub subcategory: String,
    pub text: String,
    pub use_count: i64,
}

/// Get the user styles database path.
fn user_styles_db_path() -> Result<PathBuf, Error> {
    let home = dirs::home_dir().ok_or(Error::HomeDirNotFound)?;
    Ok(home.join(".sqrl").join("user_style.db"))
}

/// Get the project memories database path.
fn project_memories_db_path(project_root: &Path) -> PathBuf {
    project_root.join(".sqrl").join("memory.db")
}

/// Read all user styles, ordered by use_count DESC.
pub fn get_user_styles() -> Result<Vec<UserStyle>, Error> {
    let db_path = user_styles_db_path()?;

    if !db_path.exists() {
        return Ok(vec![]);
    }

    let conn = Connection::open(&db_path)?;

    let mut stmt =
        conn.prepare("SELECT id, text, use_count FROM user_styles ORDER BY use_count DESC")?;

    let styles = stmt
        .query_map([], |row| {
            Ok(UserStyle {
                id: row.get(0)?,
                text: row.get(1)?,
                use_count: row.get(2)?,
            })
        })?
        .collect::<SqliteResult<Vec<_>>>()?;

    Ok(styles)
}

/// Read all project memories, ordered by use_count DESC.
pub fn get_project_memories(project_root: &Path) -> Result<Vec<ProjectMemory>, Error> {
    let db_path = project_memories_db_path(project_root);

    if !db_path.exists() {
        return Ok(vec![]);
    }

    let conn = Connection::open(&db_path)?;

    let mut stmt = conn.prepare(
        "SELECT id, category, subcategory, text, use_count
         FROM project_memories
         ORDER BY use_count DESC",
    )?;

    let memories = stmt
        .query_map([], |row| {
            Ok(ProjectMemory {
                id: row.get(0)?,
                category: row.get(1)?,
                subcategory: row.get(2)?,
                text: row.get(3)?,
                use_count: row.get(4)?,
            })
        })?
        .collect::<SqliteResult<Vec<_>>>()?;

    Ok(memories)
}

/// Read project memories grouped by category.
pub fn get_project_memories_grouped(
    project_root: &Path,
) -> Result<std::collections::HashMap<String, Vec<ProjectMemory>>, Error> {
    let memories = get_project_memories(project_root)?;

    let mut grouped: std::collections::HashMap<String, Vec<ProjectMemory>> =
        std::collections::HashMap::new();

    for memory in memories {
        grouped
            .entry(memory.category.clone())
            .or_default()
            .push(memory);
    }

    Ok(grouped)
}

/// Add a new user style.
pub fn add_user_style(text: &str) -> Result<String, Error> {
    let db_path = user_styles_db_path()?;
    let conn = Connection::open(&db_path)?;

    // Ensure table exists
    conn.execute(
        "CREATE TABLE IF NOT EXISTS user_styles (
            id TEXT PRIMARY KEY,
            text TEXT NOT NULL,
            use_count INTEGER DEFAULT 0
        )",
        [],
    )?;

    let id = uuid::Uuid::new_v4().to_string();
    conn.execute(
        "INSERT INTO user_styles (id, text, use_count) VALUES (?1, ?2, 0)",
        [&id, text],
    )?;

    Ok(id)
}

/// Delete a user style by ID.
pub fn delete_user_style(id: &str) -> Result<bool, Error> {
    let db_path = user_styles_db_path()?;
    if !db_path.exists() {
        return Ok(false);
    }

    let conn = Connection::open(&db_path)?;
    let deleted = conn.execute("DELETE FROM user_styles WHERE id = ?1", [id])?;

    Ok(deleted > 0)
}

/// Add a new project memory.
pub fn add_project_memory(
    project_root: &Path,
    category: &str,
    subcategory: &str,
    text: &str,
) -> Result<String, Error> {
    let db_path = project_memories_db_path(project_root);
    let conn = Connection::open(&db_path)?;

    // Ensure table exists
    conn.execute(
        "CREATE TABLE IF NOT EXISTS project_memories (
            id TEXT PRIMARY KEY,
            category TEXT NOT NULL,
            subcategory TEXT NOT NULL,
            text TEXT NOT NULL,
            use_count INTEGER DEFAULT 0
        )",
        [],
    )?;

    let id = uuid::Uuid::new_v4().to_string();
    conn.execute(
        "INSERT INTO project_memories (id, category, subcategory, text, use_count) VALUES (?1, ?2, ?3, ?4, 0)",
        [&id, category, subcategory, text],
    )?;

    Ok(id)
}

/// Delete a project memory by ID.
pub fn delete_project_memory(project_root: &Path, id: &str) -> Result<bool, Error> {
    let db_path = project_memories_db_path(project_root);
    if !db_path.exists() {
        return Ok(false);
    }

    let conn = Connection::open(&db_path)?;
    let deleted = conn.execute("DELETE FROM project_memories WHERE id = ?1", [id])?;

    Ok(deleted > 0)
}

// === Doc Debt (SCHEMA-006) ===

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
    let db_path = project_memories_db_path(project_root);

    // Ensure .sqrl directory exists
    if let Some(parent) = db_path.parent() {
        std::fs::create_dir_all(parent)?;
    }

    let conn = Connection::open(&db_path)?;
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
    let db_path = project_memories_db_path(project_root);

    if !db_path.exists() {
        return Ok(vec![]);
    }

    let conn = Connection::open(&db_path)?;

    // Check if table exists
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
         FROM doc_debt
         WHERE resolved = 0
         ORDER BY created_at DESC",
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

/// Mark doc debt as resolved.
pub fn resolve_doc_debt(project_root: &Path, id: &str) -> Result<bool, Error> {
    let db_path = project_memories_db_path(project_root);
    if !db_path.exists() {
        return Ok(false);
    }

    let conn = Connection::open(&db_path)?;
    let resolved_at = chrono::Utc::now().to_rfc3339();

    let updated = conn.execute(
        "UPDATE doc_debt SET resolved = 1, resolved_at = ?1 WHERE id = ?2",
        [&resolved_at, id],
    )?;

    Ok(updated > 0)
}

/// Check if doc debt exists for a commit.
pub fn has_doc_debt_for_commit(project_root: &Path, commit_sha: &str) -> Result<bool, Error> {
    let db_path = project_memories_db_path(project_root);

    if !db_path.exists() {
        return Ok(false);
    }

    let conn = Connection::open(&db_path)?;

    // Check if table exists
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

/// Format project memories as markdown (for MCP response).
pub fn format_memories_as_markdown(project_root: &Path) -> Result<String, Error> {
    let grouped = get_project_memories_grouped(project_root)?;

    if grouped.is_empty() {
        return Ok("No project memories found.".to_string());
    }

    let mut output = String::new();

    // Sort categories for consistent output
    let mut categories: Vec<_> = grouped.keys().collect();
    categories.sort();

    for category in categories {
        if let Some(memories) = grouped.get(category) {
            output.push_str(&format!("## {}\n", category));
            for memory in memories {
                output.push_str(&format!("- {}\n", memory.text));
            }
            output.push('\n');
        }
    }

    Ok(output.trim_end().to_string())
}

#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::tempdir;

    #[test]
    fn test_empty_project_memories() {
        let dir = tempdir().unwrap();
        let result = get_project_memories(dir.path());
        assert!(result.is_ok());
        assert!(result.unwrap().is_empty());
    }

    #[test]
    fn test_format_memories_empty() {
        let dir = tempdir().unwrap();
        let result = format_memories_as_markdown(dir.path());
        assert!(result.is_ok());
        assert_eq!(result.unwrap(), "No project memories found.");
    }
}
