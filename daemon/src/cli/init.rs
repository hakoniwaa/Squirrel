//! Initialize Squirrel for a project.

use std::fs;
use std::path::Path;

use tracing::{info, warn};

use crate::cli::hooks;
use crate::config::Config;
use crate::error::Error;

/// Run the init command.
pub fn run() -> Result<(), Error> {
    let project_root = std::env::current_dir()?;
    let sqrl_dir = project_root.join(".sqrl");

    if sqrl_dir.exists() {
        println!("Squirrel already initialized in this project.");
        println!("Run 'sqrl goaway' first if you want to reinitialize.");
        return Ok(());
    }

    // Create .sqrl directory
    fs::create_dir_all(&sqrl_dir)?;
    info!(path = %sqrl_dir.display(), "Created .sqrl directory");

    // Create empty database (tables created on first use)
    let db_path = sqrl_dir.join("memory.db");
    fs::write(&db_path, "")?;
    info!(path = %db_path.display(), "Created database");

    // Add .sqrl/ to .gitignore
    add_to_gitignore(&project_root)?;

    // Create config with defaults
    let config = Config::default();
    config.save(&project_root)?;
    info!("Created config.yaml");

    // Install git hooks if git exists
    if config.hooks.auto_install && hooks::has_git(&project_root) {
        if let Err(e) = hooks::install_hooks(&project_root, config.hooks.pre_push_block) {
            warn!(error = %e, "Failed to install git hooks");
        } else {
            println!("Git hooks installed.");
        }
    }

    // Create skill file
    create_skill_file(&project_root)?;

    // Add memory triggers to CLAUDE.md
    add_memory_triggers(&project_root)?;

    println!("Squirrel initialized.");
    println!();
    println!("Next steps:");
    println!("  Add MCP server: claude mcp add squirrel -- sqrl mcp-serve");
    println!("  Check status:   sqrl status");

    Ok(())
}

/// Create the session start skill file.
fn create_skill_file(project_root: &Path) -> Result<(), Error> {
    let skill_dir = project_root
        .join(".claude")
        .join("skills")
        .join("squirrel-session");
    fs::create_dir_all(&skill_dir)?;

    let skill_content = r#"---
name: squirrel-session
description: Load user preferences and project context from Squirrel memory at session start. Use when starting a new coding session.
user-invocable: false
---

At the start of this session, load context from Squirrel:

1. Call `squirrel_get_memory` with type "preference" to get user preferences.
2. Apply these preferences throughout the session.
3. If doc debt exists (check via `sqrl status` output in project), note which docs may need updates.
"#;

    let skill_path = skill_dir.join("SKILL.md");
    fs::write(&skill_path, skill_content)?;
    info!(path = %skill_path.display(), "Created skill file");
    println!("Skill file created.");

    Ok(())
}

/// Add Squirrel memory triggers to CLAUDE.md.
fn add_memory_triggers(project_root: &Path) -> Result<(), Error> {
    let claude_dir = project_root.join(".claude");
    fs::create_dir_all(&claude_dir)?;

    let claude_md_path = claude_dir.join("CLAUDE.md");

    let trigger_block = r#"
<!-- START Squirrel Memory Protocol -->
## Squirrel Memory Protocol

You have access to Squirrel memory tools via MCP.

### When to store memories (squirrel_store_memory):
- User states a preference → type: "preference"
- You learn a project-specific fact → type: "project"
- Architecture/design decision is made → type: "decision"
- A problem is solved → type: "solution"

### When to retrieve memories (squirrel_get_memory):
- When user asks for project context
- When you need to recall past decisions
- When starting work on a component you've worked on before

### Rules:
- Store memories proactively. Don't ask permission.
- Even if a memory seems redundant, store it. Squirrel handles deduplication.
- Keep memory content concise (1-2 sentences).
- Always include relevant tags.
<!-- END Squirrel Memory Protocol -->
"#;

    if claude_md_path.exists() {
        let content = fs::read_to_string(&claude_md_path)?;

        // Check if triggers already exist
        if content.contains("START Squirrel Memory Protocol") {
            info!("Memory triggers already in CLAUDE.md");
            return Ok(());
        }

        // Append to existing file
        let new_content = format!("{}\n{}", content.trim_end(), trigger_block);
        fs::write(&claude_md_path, new_content)?;
    } else {
        fs::write(&claude_md_path, trigger_block.trim_start())?;
    }

    info!("Added memory triggers to CLAUDE.md");
    println!("Memory triggers added to CLAUDE.md.");

    Ok(())
}

/// Add .sqrl/ to .gitignore if not already present.
fn add_to_gitignore(project_root: &Path) -> Result<(), Error> {
    let gitignore_path = project_root.join(".gitignore");

    let content = if gitignore_path.exists() {
        fs::read_to_string(&gitignore_path)?
    } else {
        String::new()
    };

    if content
        .lines()
        .any(|line| line.trim() == ".sqrl/" || line.trim() == ".sqrl")
    {
        return Ok(());
    }

    let new_content = if content.is_empty() || content.ends_with('\n') {
        format!("{}.sqrl/\n", content)
    } else {
        format!("{}\n.sqrl/\n", content)
    };

    fs::write(&gitignore_path, new_content)?;
    info!("Added .sqrl/ to .gitignore");

    Ok(())
}
