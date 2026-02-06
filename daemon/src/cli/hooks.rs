//! Git hook installation and management.

use std::fs;
use std::os::unix::fs::PermissionsExt;
use std::path::Path;

use tracing::info;

use crate::error::Error;

/// Pre-push hook script content.
/// Shows diff summary for AI to review before push.
const PRE_PUSH_HOOK: &str = r#"#!/bin/sh
# Squirrel: shows changes for doc review before push
# AI reads this output and decides if docs need updating

sqrl _internal docguard-check 2>/dev/null || true
"#;

/// Check if git is initialized in the project.
pub fn has_git(project_root: &Path) -> bool {
    project_root.join(".git").exists()
}

/// Check if Squirrel hooks are already installed.
#[allow(dead_code)]
pub fn hooks_installed(project_root: &Path) -> bool {
    let hooks_dir = project_root.join(".git").join("hooks");
    let pre_push = hooks_dir.join("pre-push");

    if !pre_push.exists() {
        return false;
    }

    // Check if it's our hook (contains "Squirrel")
    fs::read_to_string(&pre_push)
        .map(|content| content.contains("Squirrel"))
        .unwrap_or(false)
}

/// Install Squirrel git hooks.
pub fn install_hooks(project_root: &Path, _pre_push_block: bool) -> Result<(), Error> {
    let git_dir = project_root.join(".git");
    if !git_dir.exists() {
        return Ok(()); // No git, nothing to do
    }

    let hooks_dir = git_dir.join("hooks");
    fs::create_dir_all(&hooks_dir)?;

    // Install pre-push hook only
    let pre_push_path = hooks_dir.join("pre-push");
    install_hook(&pre_push_path, PRE_PUSH_HOOK)?;
    info!("Installed pre-push hook");

    Ok(())
}

/// Install a single hook, preserving existing hooks.
fn install_hook(path: &Path, content: &str) -> Result<(), Error> {
    let final_content = if path.exists() {
        let existing = fs::read_to_string(path)?;

        // Already has our hook
        if existing.contains("Squirrel") {
            return Ok(());
        }

        // Append to existing hook
        format!("{}\n\n{}", existing.trim(), content)
    } else {
        content.to_string()
    };

    fs::write(path, &final_content)?;

    // Make executable
    let mut perms = fs::metadata(path)?.permissions();
    perms.set_mode(0o755);
    fs::set_permissions(path, perms)?;

    Ok(())
}

/// Uninstall Squirrel git hooks.
pub fn uninstall_hooks(project_root: &Path) -> Result<(), Error> {
    let hooks_dir = project_root.join(".git").join("hooks");
    if !hooks_dir.exists() {
        return Ok(());
    }

    // Only pre-push now
    let hook_path = hooks_dir.join("pre-push");
    if hook_path.exists() {
        let content = fs::read_to_string(&hook_path)?;
        if content.contains("Squirrel") {
            // Remove our section or the entire file
            let cleaned = remove_squirrel_section(&content);
            // Check if only shebangs and whitespace remain
            let meaningful_content = cleaned
                .lines()
                .filter(|line| !line.trim().is_empty() && !line.starts_with("#!"))
                .count();
            if meaningful_content == 0 {
                fs::remove_file(&hook_path)?;
            } else {
                fs::write(&hook_path, cleaned)?;
            }
            info!("Removed Squirrel pre-push hook");
        }
    }

    // Also clean up old post-commit hook if it exists
    let post_commit_path = hooks_dir.join("post-commit");
    if post_commit_path.exists() {
        let content = fs::read_to_string(&post_commit_path)?;
        if content.contains("Squirrel") {
            let cleaned = remove_squirrel_section(&content);
            let meaningful_content = cleaned
                .lines()
                .filter(|line| !line.trim().is_empty() && !line.starts_with("#!"))
                .count();
            if meaningful_content == 0 {
                fs::remove_file(&post_commit_path)?;
            } else {
                fs::write(&post_commit_path, cleaned)?;
            }
            info!("Removed old Squirrel post-commit hook");
        }
    }

    Ok(())
}

/// Remove Squirrel section from hook content.
fn remove_squirrel_section(content: &str) -> String {
    content
        .lines()
        .filter(|line| {
            !line.contains("Squirrel") && !line.contains("sqrl _internal") && !line.contains("doc")
        })
        .collect::<Vec<_>>()
        .join("\n")
}
