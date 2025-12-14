//! Show daemon and memory stats.

use crate::config::{Config, ProjectsRegistry};
use crate::db::Database;
use crate::error::Error;

/// Run status command.
pub async fn run() -> Result<(), Error> {
    println!("Squirrel Status");
    println!("===============");
    println!();

    // Config paths
    println!("Paths:");
    println!("  Config: {}", Config::path().display());
    println!("  Global DB: {}", Config::global_db_path().display());
    println!();

    // Global database stats
    let global_db_path = Config::global_db_path();
    if global_db_path.exists() {
        let db = Database::open(&global_db_path)?;
        print_db_stats(&db, "Global")?;
    } else {
        println!("Global database: not initialized");
    }
    println!();

    // Projects
    let registry = ProjectsRegistry::load()?;
    println!("Registered Projects: {}", registry.projects.len());
    for project in &registry.projects {
        println!(
            "  - {} ({})",
            project.project_id,
            project.root_path.display()
        );
    }
    println!();

    // Current directory project
    let cwd = std::env::current_dir()?;
    let local_db_path = cwd.join(".sqrl").join("squirrel.db");
    if local_db_path.exists() {
        let db = Database::open(&local_db_path)?;
        print_db_stats(&db, "Project")?;
    }

    // Daemon status
    let socket_path = Config::load()?.daemon.socket_path;
    if std::path::Path::new(&socket_path).exists() {
        println!("Daemon: running (socket: {})", socket_path);
    } else {
        println!("Daemon: not running");
    }

    Ok(())
}

fn print_db_stats(db: &Database, label: &str) -> Result<(), Error> {
    // Memory counts by status
    let mut stmt = db
        .conn()
        .prepare("SELECT status, COUNT(*) as count FROM memories GROUP BY status")?;
    let mut rows = stmt.query([])?;

    println!("{} Memories:", label);
    let mut total = 0;
    while let Some(row) = rows.next()? {
        let status: String = row.get("status")?;
        let count: i32 = row.get("count")?;
        println!("  {}: {}", status, count);
        total += count;
    }
    println!("  Total: {}", total);

    // Episode counts
    let mut stmt = db
        .conn()
        .prepare("SELECT processed, COUNT(*) as count FROM episodes GROUP BY processed")?;
    let mut rows = stmt.query([])?;

    println!("Episodes:");
    while let Some(row) = rows.next()? {
        let processed: i32 = row.get("processed")?;
        let count: i32 = row.get("count")?;
        let label = if processed == 0 {
            "pending"
        } else {
            "processed"
        };
        println!("  {}: {}", label, count);
    }

    Ok(())
}
