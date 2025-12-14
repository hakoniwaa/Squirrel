//! Import memories from JSON.

use crate::config::Config;
use crate::db::{Database, Memory};
use crate::error::Error;

/// Run import command.
pub async fn run(file: &str) -> Result<(), Error> {
    let content = std::fs::read_to_string(file)?;
    let data: serde_json::Value = serde_json::from_str(&content)?;

    let memories = data["memories"]
        .as_array()
        .ok_or_else(|| Error::other("Invalid JSON: missing 'memories' array"))?;

    let db_path = Config::global_db_path();
    if let Some(parent) = db_path.parent() {
        std::fs::create_dir_all(parent)?;
    }
    let db = Database::open(&db_path)?;

    let mut imported = 0;
    let mut skipped = 0;

    for m in memories {
        let id = m["id"].as_str().ok_or_else(|| Error::other("Missing id"))?;

        // Skip if already exists
        if db.get_memory(id)?.is_some() {
            skipped += 1;
            continue;
        }

        let memory = Memory {
            id: id.to_string(),
            project_id: m["project_id"].as_str().map(|s| s.to_string()),
            scope: m["scope"].as_str().unwrap_or("global").to_string(),
            owner_type: m["owner_type"].as_str().unwrap_or("user").to_string(),
            owner_id: m["owner_id"].as_str().unwrap_or("default").to_string(),
            kind: m["kind"].as_str().unwrap_or("note").to_string(),
            tier: m["tier"].as_str().unwrap_or("short_term").to_string(),
            polarity: m["polarity"].as_i64().unwrap_or(1) as i32,
            key: m["key"].as_str().map(|s| s.to_string()),
            text: m["text"]
                .as_str()
                .ok_or_else(|| Error::other("Missing text"))?
                .to_string(),
            status: m["status"].as_str().unwrap_or("provisional").to_string(),
            confidence: m["confidence"].as_f64(),
            expires_at: m["expires_at"].as_str().map(|s| s.to_string()),
            embedding: None,
            created_at: m["created_at"]
                .as_str()
                .unwrap_or(&chrono::Utc::now().to_rfc3339())
                .to_string(),
            updated_at: m["updated_at"]
                .as_str()
                .unwrap_or(&chrono::Utc::now().to_rfc3339())
                .to_string(),
        };

        db.insert_memory(&memory)?;
        imported += 1;
    }

    println!(
        "Imported {} memories, skipped {} duplicates",
        imported, skipped
    );

    Ok(())
}
