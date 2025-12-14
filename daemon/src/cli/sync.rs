//! Sync all projects with CLI configs.

use crate::config::ProjectsRegistry;
use crate::error::Error;

/// Run sync command.
pub async fn run() -> Result<(), Error> {
    println!("Syncing projects...");

    let registry = ProjectsRegistry::load()?;

    for project in &registry.projects {
        let sqrl_dir = project.root_path.join(".sqrl");

        if !sqrl_dir.exists() {
            println!(
                "  {} - missing .sqrl directory, skipping",
                project.project_id
            );
            continue;
        }

        // TODO: Sync agent configs (CLAUDE.md, .cursorrules, etc.)
        println!("  {} - synced", project.project_id);
    }

    println!("Sync complete.");
    Ok(())
}
