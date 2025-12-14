//! Soft delete (deprecate) memories.

use crate::config::Config;
use crate::db::Database;
use crate::error::Error;

/// Run forget command.
pub async fn run(id: Option<&str>, query: Option<&str>, confirm: bool) -> Result<(), Error> {
    let db_path = Config::global_db_path();
    if !db_path.exists() {
        return Err(Error::not_initialized("No database found"));
    }

    let db = Database::open(&db_path)?;

    let memory_id = if let Some(id) = id {
        // Direct ID lookup
        id.to_string()
    } else if let Some(q) = query {
        // Search for memory
        let mut stmt = db.conn().prepare(
            "SELECT id, text FROM memories WHERE text LIKE ? AND status != 'deprecated' LIMIT 1",
        )?;
        let pattern = format!("%{}%", q);
        let mut rows = stmt.query([&pattern])?;

        if let Some(row) = rows.next()? {
            let id: String = row.get("id")?;
            let text: String = row.get("text")?;
            println!("Found memory: {}", text);
            id
        } else {
            println!("No memory found matching '{}'", q);
            return Ok(());
        }
    } else {
        println!("Please provide --id or --query");
        return Ok(());
    };

    // Check if memory exists
    if let Some(memory) = db.get_memory(&memory_id)? {
        if !confirm {
            println!("Memory to deprecate:");
            println!("  ID: {}", &memory.id[..8]);
            println!("  Text: {}", memory.text);
            println!();
            println!("Run with --confirm to deprecate this memory.");
            return Ok(());
        }

        db.deprecate_memory(&memory_id)?;
        println!("Memory {} deprecated.", &memory_id[..8]);
    } else {
        println!("Memory not found: {}", memory_id);
    }

    Ok(())
}
