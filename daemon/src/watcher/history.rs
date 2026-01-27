//! Process historical Claude Code logs.

use std::fs;
use std::path::{Path, PathBuf};

use chrono::{DateTime, Duration, Utc};
use tracing::{debug, info, warn};

use crate::error::Error;
use crate::ipc::{IpcClient, ProcessEpisodeRequest};
use crate::watcher::{LogParser, SessionTracker};

/// Find the Claude projects directory.
fn claude_projects_dir() -> Option<PathBuf> {
    dirs::home_dir().map(|h| h.join(".claude").join("projects"))
}

/// Convert a project path to Claude's directory name format.
/// Claude uses the path with slashes replaced by dashes.
/// e.g., /home/user/projects/myapp -> -home-user-projects-myapp
fn project_path_to_claude_dir(project_path: &Path) -> String {
    let path_str = project_path.to_string_lossy();
    path_str.replace('/', "-").replace('\\', "-")
}

/// Find log files for a project, filtered by age.
fn find_log_files(project_path: &Path, max_age_days: u32) -> Result<Vec<PathBuf>, Error> {
    let claude_dir = claude_projects_dir().ok_or(Error::HomeDirNotFound)?;

    let project_dir_name = project_path_to_claude_dir(project_path);
    let project_logs_dir = claude_dir.join(&project_dir_name);

    if !project_logs_dir.exists() {
        debug!(
            path = %project_logs_dir.display(),
            "No Claude logs directory found for this project"
        );
        return Ok(vec![]);
    }

    let cutoff = Utc::now() - Duration::days(max_age_days as i64);
    let mut log_files = Vec::new();

    for entry in fs::read_dir(&project_logs_dir)? {
        let entry = entry?;
        let path = entry.path();

        if path.extension().is_some_and(|e| e == "jsonl") {
            // Check file modification time
            if let Ok(metadata) = entry.metadata() {
                if let Ok(modified) = metadata.modified() {
                    let modified: DateTime<Utc> = modified.into();
                    if modified >= cutoff {
                        log_files.push(path);
                    }
                }
            }
        }
    }

    // Sort by modification time (oldest first for chronological processing)
    log_files.sort_by(|a, b| {
        let a_time = fs::metadata(a)
            .and_then(|m| m.modified())
            .unwrap_or(std::time::SystemTime::UNIX_EPOCH);
        let b_time = fs::metadata(b)
            .and_then(|m| m.modified())
            .unwrap_or(std::time::SystemTime::UNIX_EPOCH);
        a_time.cmp(&b_time)
    });

    Ok(log_files)
}

/// Process historical logs for a project.
pub async fn process_history(
    project_path: &Path,
    max_age_days: u32,
    ipc_client: &IpcClient,
) -> Result<ProcessingStats, Error> {
    let log_files = find_log_files(project_path, max_age_days)?;

    if log_files.is_empty() {
        info!("No historical logs found to process");
        return Ok(ProcessingStats::default());
    }

    info!(
        count = log_files.len(),
        days = max_age_days,
        "Found historical log files"
    );

    let mut stats = ProcessingStats::default();
    let parser = LogParser::new();
    let mut tracker = SessionTracker::new();

    for log_file in &log_files {
        debug!(file = %log_file.display(), "Processing historical log file");

        let content = match fs::read_to_string(log_file) {
            Ok(c) => c,
            Err(e) => {
                warn!(file = %log_file.display(), error = %e, "Failed to read log file");
                stats.files_failed += 1;
                continue;
            }
        };

        // Parse all entries in the file
        for line in content.lines() {
            if line.trim().is_empty() {
                continue;
            }

            match parser.parse_line(line) {
                Ok(entry) => {
                    stats.entries_parsed += 1;

                    // Accumulate entry in session tracker (all flushed at end)
                    tracker.process_entry(entry);
                }
                Err(e) => {
                    // Skip invalid entries silently (common for summary entries etc.)
                    debug!(error = %e, "Skipping invalid log entry");
                }
            }
        }

        stats.files_processed += 1;
    }

    // Flush any remaining sessions
    let remaining = tracker.flush_all();
    for session in remaining {
        stats.sessions_found += 1;
        if !session.events.is_empty() {
            let request = ProcessEpisodeRequest {
                project_id: session.project_id,
                project_root: session.project_root,
                events: session.events,
                existing_user_styles: vec![],
                existing_project_memories: vec![],
            };

            match ipc_client.process_episode(request).await {
                Ok(_) => {
                    stats.sessions_processed += 1;
                }
                Err(e) => {
                    warn!(
                        session_id = %session.session_id,
                        error = %e,
                        "Failed to process historical session"
                    );
                    stats.sessions_failed += 1;
                }
            }
        }
    }

    Ok(stats)
}

/// Statistics from history processing.
#[derive(Debug, Default)]
pub struct ProcessingStats {
    pub files_processed: usize,
    pub files_failed: usize,
    pub entries_parsed: usize,
    pub sessions_found: usize,
    pub sessions_processed: usize,
    pub sessions_failed: usize,
}

impl std::fmt::Display for ProcessingStats {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(
            f,
            "Processed {} files ({} failed), {} sessions ({} sent, {} failed)",
            self.files_processed,
            self.files_failed,
            self.sessions_found,
            self.sessions_processed,
            self.sessions_failed
        )
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_project_path_to_claude_dir() {
        assert_eq!(
            project_path_to_claude_dir(Path::new("/home/user/projects/myapp")),
            "-home-user-projects-myapp"
        );

        assert_eq!(
            project_path_to_claude_dir(Path::new("/Users/alice/code/test")),
            "-Users-alice-code-test"
        );
    }
}
