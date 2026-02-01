//! Show Squirrel status.

use std::path::Path;

use crate::error::Error;
use crate::storage;

/// Run the status command. Returns exit code.
pub fn run() -> Result<i32, Error> {
    let project_root = std::env::current_dir()?;
    let sqrl_dir = project_root.join(".sqrl");

    println!("Squirrel Status");
    println!("  Project: {}", project_root.display());

    if !sqrl_dir.exists() {
        println!("  Initialized: no");
        println!();
        println!("Run 'sqrl init' to initialize Squirrel for this project.");
        return Ok(1);
    }

    println!("  Initialized: yes");

    // Memory counts
    let counts = storage::get_memory_counts(&project_root)?;
    let total: i64 = counts.values().sum();
    if total > 0 {
        let mut parts: Vec<String> = counts.iter().map(|(k, v)| format!("{} {}", v, k)).collect();
        parts.sort();
        println!("  Memories: {} total ({})", total, parts.join(", "));
    } else {
        println!("  Memories: 0");
    }

    // Doc debt
    let debts = storage::get_unresolved_doc_debt(&project_root).unwrap_or_default();
    if debts.is_empty() {
        println!("  Doc debt: none");
    } else {
        println!("  Doc debt: {} pending", debts.len());
    }

    // Last activity
    if let Some(last_activity) = get_last_activity(&sqrl_dir) {
        println!("  Last activity: {}", last_activity);
    }

    // Show doc debt details if any
    if !debts.is_empty() {
        println!();
        println!("Doc Debt:");
        for debt in &debts {
            let short_sha = &debt.commit_sha[..7.min(debt.commit_sha.len())];
            let msg = debt.commit_message.as_deref().unwrap_or("(no message)");
            println!("  {} {}", short_sha, msg);
            println!("    Expected: {}", debt.expected_docs.join(", "));
        }
    }

    Ok(0)
}

/// Get last activity time as human-readable string.
fn get_last_activity(sqrl_dir: &Path) -> Option<String> {
    let db_path = sqrl_dir.join("memory.db");

    let modified = std::fs::metadata(&db_path)
        .ok()
        .and_then(|m| m.modified().ok())?;

    let duration = std::time::SystemTime::now().duration_since(modified).ok()?;

    let secs = duration.as_secs();

    let human = if secs < 60 {
        "just now".to_string()
    } else if secs < 3600 {
        let mins = secs / 60;
        format!("{} minute{} ago", mins, if mins == 1 { "" } else { "s" })
    } else if secs < 86400 {
        let hours = secs / 3600;
        format!("{} hour{} ago", hours, if hours == 1 { "" } else { "s" })
    } else {
        let days = secs / 86400;
        format!("{} day{} ago", days, if days == 1 { "" } else { "s" })
    };

    Some(human)
}
