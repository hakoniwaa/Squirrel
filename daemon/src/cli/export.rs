//! Export memories as JSON.

use crate::config::Config;
use crate::db::Database;
use crate::error::Error;

/// Run export command.
pub async fn run(kind: Option<&str>, project: bool) -> Result<(), Error> {
    let db_path = if project {
        let cwd = std::env::current_dir()?;
        cwd.join(".sqrl").join("squirrel.db")
    } else {
        Config::global_db_path()
    };

    if !db_path.exists() {
        println!("No database found at {}", db_path.display());
        return Ok(());
    }

    let db = Database::open(&db_path)?;

    // Build query
    let mut sql = String::from(
        "SELECT id, project_id, scope, owner_type, owner_id, kind, tier, \
         polarity, key, text, status, confidence, expires_at, created_at, updated_at \
         FROM memories WHERE status != 'deprecated'",
    );

    if let Some(k) = kind {
        sql.push_str(&format!(" AND kind = '{}'", k));
    }

    sql.push_str(" ORDER BY created_at DESC");

    let mut stmt = db.conn().prepare(&sql)?;
    let mut rows = stmt.query([])?;

    let mut memories: Vec<serde_json::Value> = Vec::new();

    while let Some(row) = rows.next()? {
        let memory = serde_json::json!({
            "id": row.get::<_, String>("id")?,
            "project_id": row.get::<_, Option<String>>("project_id")?,
            "scope": row.get::<_, String>("scope")?,
            "owner_type": row.get::<_, String>("owner_type")?,
            "owner_id": row.get::<_, String>("owner_id")?,
            "kind": row.get::<_, String>("kind")?,
            "tier": row.get::<_, String>("tier")?,
            "polarity": row.get::<_, i32>("polarity")?,
            "key": row.get::<_, Option<String>>("key")?,
            "text": row.get::<_, String>("text")?,
            "status": row.get::<_, String>("status")?,
            "confidence": row.get::<_, Option<f64>>("confidence")?,
            "expires_at": row.get::<_, Option<String>>("expires_at")?,
            "created_at": row.get::<_, String>("created_at")?,
            "updated_at": row.get::<_, String>("updated_at")?,
        });
        memories.push(memory);
    }

    let output = serde_json::json!({
        "version": "1.0",
        "exported_at": chrono::Utc::now().to_rfc3339(),
        "memories": memories,
    });

    println!("{}", serde_json::to_string_pretty(&output)?);

    Ok(())
}
