//! Manage memory policy.

use crate::error::Error;

/// Run policy command.
pub async fn run(action: &str) -> Result<(), Error> {
    match action {
        "show" => {
            // Check for project policy first
            let cwd = std::env::current_dir()?;
            let project_policy = cwd.join(".sqrl").join("policy.toml");
            let global_policy = dirs::home_dir()
                .unwrap_or_else(|| std::path::PathBuf::from("."))
                .join(".sqrl")
                .join("policy.toml");

            if project_policy.exists() {
                println!("Project Policy: {}", project_policy.display());
                let content = std::fs::read_to_string(&project_policy)?;
                println!("{}", content);
            } else if global_policy.exists() {
                println!("Global Policy: {}", global_policy.display());
                let content = std::fs::read_to_string(&global_policy)?;
                println!("{}", content);
            } else {
                println!("No policy file found.");
                println!();
                println!("Create one at:");
                println!("  Project: .sqrl/policy.toml");
                println!("  Global: ~/.sqrl/policy.toml");
            }
        }

        "reload" => {
            // TODO: Signal daemon to reload policy
            println!("Policy reload not yet implemented.");
            println!("Restart the daemon to apply policy changes.");
        }

        _ => {
            println!("Unknown action: {}", action);
            println!("Usage: sqrl policy [show|reload]");
        }
    }

    Ok(())
}
