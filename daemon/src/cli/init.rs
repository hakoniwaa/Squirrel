//! Initialize project for Squirrel.

use std::path::PathBuf;

use crate::config::{ProjectConfig, ProjectsRegistry};
use crate::db::Database;
use crate::error::Error;

/// Run project initialization.
pub async fn run(skip_history: bool) -> Result<(), Error> {
    let cwd = std::env::current_dir()?;
    println!("Initializing Squirrel in: {}", cwd.display());

    // Create .sqrl directory
    let sqrl_dir = cwd.join(".sqrl");
    std::fs::create_dir_all(&sqrl_dir)?;

    // Initialize database
    let db_path = sqrl_dir.join("squirrel.db");
    let _db = Database::open(&db_path)?;
    println!("Created database: {}", db_path.display());

    // Generate project ID from path
    let project_id = generate_project_id(&cwd);

    // Register project
    let mut registry = ProjectsRegistry::load()?;
    registry.register(ProjectConfig {
        project_id: project_id.clone(),
        root_path: cwd.clone(),
        initialized_at: chrono::Utc::now().to_rfc3339(),
    });
    registry.save()?;
    println!("Registered project: {}", project_id);

    if !skip_history {
        println!("Scanning for historical logs...");
        // TODO: Implement historical log ingestion
        println!("Historical log ingestion not yet implemented");
    }

    println!("Squirrel initialized successfully!");
    Ok(())
}

fn generate_project_id(path: &PathBuf) -> String {
    // Use directory name as project ID
    path.file_name()
        .and_then(|n| n.to_str())
        .map(|s| s.to_string())
        .unwrap_or_else(|| uuid::Uuid::new_v4().to_string())
}
