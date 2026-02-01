//! Remove Squirrel from a project.

use std::fs;
use std::io::{self, Write};

use tracing::warn;

use crate::cli::hooks;
use crate::error::Error;

/// Run the goaway command.
pub fn run(force: bool) -> Result<(), Error> {
    let project_root = std::env::current_dir()?;
    let sqrl_dir = project_root.join(".sqrl");

    if !sqrl_dir.exists() {
        println!("No .sqrl/ directory found in this project.");
        return Ok(());
    }

    // Show what will be removed
    println!("This will remove:");
    println!("  .sqrl/ ({})", sqrl_dir.display());
    print_dir_contents(&sqrl_dir, 4)?;

    let skill_dir = project_root
        .join(".claude")
        .join("skills")
        .join("squirrel-session");
    if skill_dir.exists() {
        println!("  .claude/skills/squirrel-session/");
    }

    // Confirm unless --force
    if !force {
        print!("\nAre you sure? [y/N] ");
        io::stdout().flush()?;

        let mut input = String::new();
        io::stdin().read_line(&mut input)?;

        if !input.trim().eq_ignore_ascii_case("y") {
            println!("Cancelled.");
            return Ok(());
        }
    }

    // Uninstall git hooks
    if hooks::has_git(&project_root) {
        if let Err(e) = hooks::uninstall_hooks(&project_root) {
            warn!(error = %e, "Failed to uninstall git hooks");
        } else {
            println!("Git hooks removed.");
        }
    }

    // Remove skill directory
    if skill_dir.exists() {
        fs::remove_dir_all(&skill_dir)?;
        println!("Skill file removed.");
    }

    // Remove memory triggers from CLAUDE.md
    remove_memory_triggers(&project_root);

    // Remove .sqrl/ directory
    fs::remove_dir_all(&sqrl_dir)?;
    println!("Removed .sqrl/");
    println!("Squirrel has left the building.");

    Ok(())
}

/// Remove Squirrel memory triggers from CLAUDE.md.
fn remove_memory_triggers(project_root: &std::path::Path) {
    let claude_md_path = project_root.join(".claude").join("CLAUDE.md");
    if !claude_md_path.exists() {
        return;
    }

    if let Ok(content) = fs::read_to_string(&claude_md_path) {
        if let (Some(start), Some(end)) = (
            content.find("<!-- START Squirrel Memory Protocol -->"),
            content.find("<!-- END Squirrel Memory Protocol -->"),
        ) {
            let end = end + "<!-- END Squirrel Memory Protocol -->".len();
            let mut new_content = String::new();
            new_content.push_str(content[..start].trim_end());
            let after = content[end..].trim_start();
            if !after.is_empty() {
                new_content.push_str("\n\n");
                new_content.push_str(after);
            }
            new_content.push('\n');

            if let Err(e) = fs::write(&claude_md_path, new_content) {
                warn!(error = %e, "Failed to clean CLAUDE.md");
            } else {
                println!("Memory triggers removed from CLAUDE.md.");
            }
        }
    }
}

fn print_dir_contents(path: &std::path::Path, indent: usize) -> Result<(), Error> {
    let indent_str = " ".repeat(indent);
    if let Ok(entries) = fs::read_dir(path) {
        for entry in entries.flatten() {
            let name = entry.file_name();
            let metadata = entry.metadata()?;
            if metadata.is_dir() {
                println!("{}{}/", indent_str, name.to_string_lossy());
            } else {
                let size = metadata.len();
                println!(
                    "{}{} ({})",
                    indent_str,
                    name.to_string_lossy(),
                    format_size(size)
                );
            }
        }
    }
    Ok(())
}

fn format_size(bytes: u64) -> String {
    if bytes < 1024 {
        format!("{} B", bytes)
    } else if bytes < 1024 * 1024 {
        format!("{:.1} KB", bytes as f64 / 1024.0)
    } else {
        format!("{:.1} MB", bytes as f64 / (1024.0 * 1024.0))
    }
}
