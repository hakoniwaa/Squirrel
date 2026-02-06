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
        if let Err(e) = hooks::install_hooks(&project_root, false) {
            warn!(error = %e, "Failed to install git hooks");
        } else {
            println!("Git hooks installed.");
        }
    }

    // Create skill file
    create_skill_file(&project_root)?;

    // Add memory triggers to CLAUDE.md
    add_memory_triggers(&project_root)?;

    // Register MCP server with enabled tools
    register_mcp_servers(&config)?;

    println!("Squirrel initialized.");
    println!();
    println!("Next steps:");
    println!("  Check status: sqrl status");

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
description: Load behavioral corrections from Squirrel memory at session start. Use when starting a new coding session.
user-invocable: false
---

At the start of this session, load corrections from Squirrel:

1. Call `squirrel_get_memory` to get all behavioral corrections.
2. Apply these corrections throughout the session.
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

You have access to Squirrel memory tools via MCP. Memories are **behavioral corrections** — things that change how you act next time.

### When to store (squirrel_store_memory):
- User corrects your behavior → type: "preference" (e.g., "Don't use emojis in commits")
- You learn a project-specific rule → type: "project" (e.g., "Use httpx not requests here")
- A choice is made that constrains future work → type: "decision" (e.g., "We chose SQLite, don't suggest Postgres")
- You hit an error and find the fix → type: "solution" (e.g., "SSL error with requests? Switch to httpx")

### When NOT to store:
- Research in progress (no decision made yet)
- General knowledge (not project-specific)
- Conversation context (already in chat history)
- Anything that doesn't change your future behavior

### When to retrieve (squirrel_get_memory):
- At session start (via squirrel-session skill)
- Before making choices the user may have corrected before

### Rules:
- Store corrections proactively when the user corrects you. Don't ask permission.
- Every memory should be an actionable instruction: "Do X" or "Don't do Y" or "When Z, do W".
- Keep content concise (1-2 sentences).
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

/// Register Squirrel as an MCP server with enabled AI tools.
fn register_mcp_servers(config: &Config) -> Result<(), Error> {
    let sqrl_bin = std::env::current_exe()?
        .canonicalize()
        .unwrap_or_else(|_| std::env::current_exe().unwrap());

    if config.tools.claude_code {
        register_claude_code_mcp(&sqrl_bin)?;
    }

    // Future: cursor, codex registration

    Ok(())
}

/// Register with Claude Code via `claude mcp add`.
fn register_claude_code_mcp(sqrl_bin: &Path) -> Result<(), Error> {
    use std::process::Command;

    // Check if claude CLI exists
    let which = Command::new("which").arg("claude").output();
    if which.is_err() || !which.unwrap().status.success() {
        warn!("Claude Code CLI not found, skipping MCP registration");
        return Ok(());
    }

    let output = Command::new("claude")
        .args([
            "mcp",
            "add",
            "squirrel",
            "-s",
            "project",
            "--",
            sqrl_bin.to_str().unwrap(),
            "mcp-serve",
        ])
        .output()?;

    if output.status.success() {
        info!("Registered MCP server with Claude Code");
        println!("MCP server registered with Claude Code.");
    } else {
        let stderr = String::from_utf8_lossy(&output.stderr);
        warn!(stderr = %stderr, "Failed to register MCP server with Claude Code");
        println!(
            "Could not auto-register MCP server. Run manually:\n  claude mcp add squirrel -- {} mcp-serve",
            sqrl_bin.display()
        );
    }

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
