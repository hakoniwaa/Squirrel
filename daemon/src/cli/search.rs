//! Search memories.

use crate::config::Config;
use crate::db::Database;
use crate::error::Error;

/// Run memory search.
pub async fn run(query: &str, kind: Option<&str>, tier: Option<&str>) -> Result<(), Error> {
    let db_path = Config::global_db_path();
    if !db_path.exists() {
        println!("No memories found. Run 'sqrl init' first.");
        return Ok(());
    }

    let db = Database::open(&db_path)?;

    // Build query
    let mut sql = String::from("SELECT * FROM memories WHERE status IN ('provisional', 'active')");
    let mut params: Vec<String> = Vec::new();

    if let Some(k) = kind {
        sql.push_str(" AND kind = ?");
        params.push(k.to_string());
    }

    if let Some(t) = tier {
        sql.push_str(" AND tier = ?");
        params.push(t.to_string());
    }

    // Text search (simple LIKE for now, vector search later)
    sql.push_str(" AND text LIKE ?");
    params.push(format!("%{}%", query));

    sql.push_str(" ORDER BY updated_at DESC LIMIT 20");

    let mut stmt = db.conn().prepare(&sql)?;
    let param_refs: Vec<&dyn rusqlite::ToSql> =
        params.iter().map(|s| s as &dyn rusqlite::ToSql).collect();
    let mut rows = stmt.query(param_refs.as_slice())?;

    let mut count = 0;
    while let Some(row) = rows.next()? {
        let id: String = row.get("id")?;
        let kind: String = row.get("kind")?;
        let tier: String = row.get("tier")?;
        let text: String = row.get("text")?;
        let status: String = row.get("status")?;

        println!("---");
        println!("ID: {}", &id[..8]);
        println!("Kind: {} | Tier: {} | Status: {}", kind, tier, status);
        println!("Text: {}", text);
        count += 1;
    }

    if count == 0 {
        println!("No memories found matching '{}'", query);
    } else {
        println!("---");
        println!("Found {} memories", count);
    }

    Ok(())
}
