//! Hidden internal commands for git hooks.

use std::path::PathBuf;
use std::process::Command;

use tracing::debug;

use crate::error::Error;

/// Show diff summary before push (called by pre-push hook).
/// AI reads this output and decides if docs need updating.
pub fn docguard_check() -> Result<bool, Error> {
    // Find project root
    let project_root = match find_project_root() {
        Some(path) => path,
        None => {
            // Not a Squirrel project, allow push
            return Ok(true);
        }
    };

    // Get commits that will be pushed
    let commits = get_unpushed_commits();
    if commits.is_empty() {
        // Nothing to push
        return Ok(true);
    }

    // Get combined diff stats
    let diff_stats = get_diff_stats_for_push();
    if diff_stats.is_empty() {
        return Ok(true);
    }

    // Find doc files in the project
    let doc_files = find_doc_files(&project_root);

    // Print the summary for AI to review
    println!();
    println!("═══════════════════════════════════════════════════════════════");
    println!(" Squirrel: Review changes before push");
    println!("═══════════════════════════════════════════════════════════════");
    println!();
    println!(" Commits to push: {}", commits.len());
    println!();
    println!(" Files changed:");
    for stat in &diff_stats {
        println!("   {}", stat);
    }
    println!();

    if !doc_files.is_empty() {
        println!(" Doc files in repo:");
        for doc in &doc_files {
            println!("   {}", doc);
        }
        println!();
    }

    println!(" → Review if any docs need updating based on these changes.");
    println!("═══════════════════════════════════════════════════════════════");
    println!();

    // Always allow push - this is informational only
    Ok(true)
}

/// Find project root by walking up directories looking for .sqrl.
fn find_project_root() -> Option<PathBuf> {
    let cwd = std::env::current_dir().ok()?;
    let mut current = cwd.as_path();

    loop {
        if current.join(".sqrl").exists() {
            return Some(current.to_path_buf());
        }
        current = current.parent()?;
    }
}

/// Get list of commits that will be pushed (not yet on remote).
fn get_unpushed_commits() -> Vec<String> {
    // Get the upstream branch
    let upstream = Command::new("git")
        .args(["rev-parse", "--abbrev-ref", "@{upstream}"])
        .output();

    let upstream_ref = match upstream {
        Ok(out) if out.status.success() => String::from_utf8_lossy(&out.stdout).trim().to_string(),
        _ => {
            // No upstream, compare against origin/main or origin/master
            let main_exists = Command::new("git")
                .args(["rev-parse", "--verify", "origin/main"])
                .output()
                .map(|o| o.status.success())
                .unwrap_or(false);

            if main_exists {
                "origin/main".to_string()
            } else {
                "origin/master".to_string()
            }
        }
    };

    // Get commits between upstream and HEAD
    let output = Command::new("git")
        .args(["log", "--oneline", &format!("{}..HEAD", upstream_ref)])
        .output();

    match output {
        Ok(out) if out.status.success() => String::from_utf8_lossy(&out.stdout)
            .lines()
            .map(String::from)
            .collect(),
        _ => vec![],
    }
}

/// Get diff stats for changes being pushed.
fn get_diff_stats_for_push() -> Vec<String> {
    // Get the upstream branch
    let upstream = Command::new("git")
        .args(["rev-parse", "--abbrev-ref", "@{upstream}"])
        .output();

    let upstream_ref = match upstream {
        Ok(out) if out.status.success() => String::from_utf8_lossy(&out.stdout).trim().to_string(),
        _ => {
            let main_exists = Command::new("git")
                .args(["rev-parse", "--verify", "origin/main"])
                .output()
                .map(|o| o.status.success())
                .unwrap_or(false);

            if main_exists {
                "origin/main".to_string()
            } else {
                "origin/master".to_string()
            }
        }
    };

    // Get diff stat
    let output = Command::new("git")
        .args([
            "diff",
            "--stat",
            "--stat-width=60",
            &format!("{}..HEAD", upstream_ref),
        ])
        .output();

    match output {
        Ok(out) if out.status.success() => {
            let stdout = String::from_utf8_lossy(&out.stdout);
            stdout
                .lines()
                .filter(|line| !line.trim().is_empty())
                .filter(|line| !line.contains("files changed"))
                .filter(|line| !line.contains("file changed"))
                .map(|line| line.trim().to_string())
                .collect()
        }
        _ => vec![],
    }
}

/// Find documentation files in the project.
fn find_doc_files(project_root: &PathBuf) -> Vec<String> {
    let mut docs = Vec::new();

    // Common doc locations
    let doc_patterns = [
        "README.md",
        "CHANGELOG.md",
        "docs/*.md",
        "specs/*.md",
        ".claude/*.md",
        "*.md",
    ];

    for pattern in &doc_patterns {
        if let Ok(entries) = glob::glob(&project_root.join(pattern).to_string_lossy()) {
            for entry in entries.flatten() {
                if let Ok(relative) = entry.strip_prefix(project_root) {
                    let path_str = relative.to_string_lossy().to_string();
                    // Skip node_modules, target, etc.
                    if !path_str.contains("node_modules")
                        && !path_str.contains("target/")
                        && !path_str.contains(".git/")
                        && !docs.contains(&path_str)
                    {
                        docs.push(path_str);
                    }
                }
            }
        }
    }

    docs.sort();
    debug!(count = docs.len(), "Found doc files");
    docs
}
