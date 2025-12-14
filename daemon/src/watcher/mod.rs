//! Log file watcher for AI agent interactions.
//!
//! Watches for changes to Claude, Cursor, and other AI tool log files.

use std::collections::HashMap;
use std::path::{Path, PathBuf};

use notify::{Event, RecommendedWatcher, RecursiveMode, Watcher};
use tokio::sync::mpsc;

use crate::config::Config;
use crate::error::Error;

/// Log watcher for AI agent files.
pub struct LogWatcher {
    config: Config,
    watcher: RecommendedWatcher,
    rx: mpsc::Receiver<Result<Event, notify::Error>>,
    watched_paths: HashMap<PathBuf, String>, // path -> project_id
}

impl LogWatcher {
    /// Create a new log watcher.
    pub fn new(config: &Config) -> Result<Self, Error> {
        let (tx, rx) = mpsc::channel(100);

        let watcher = notify::recommended_watcher(move |res| {
            let _ = tx.blocking_send(res);
        })
        .map_err(|e| Error::Watcher(e.to_string()))?;

        Ok(Self {
            config: config.clone(),
            watcher,
            rx,
            watched_paths: HashMap::new(),
        })
    }

    /// Add a project to watch.
    pub fn watch_project(&mut self, project_path: &Path) -> Result<(), Error> {
        let project_id = project_path
            .file_name()
            .and_then(|n| n.to_str())
            .map(|s| s.to_string())
            .unwrap_or_else(|| "unknown".to_string());

        // Watch .claude directory if Claude is enabled
        if self.config.agents.claude {
            let claude_dir = project_path.join(".claude");
            if claude_dir.exists() {
                self.watcher
                    .watch(&claude_dir, RecursiveMode::Recursive)
                    .map_err(|e| Error::Watcher(e.to_string()))?;
                self.watched_paths.insert(claude_dir, project_id.clone());
                tracing::debug!("Watching .claude in {}", project_path.display());
            }
        }

        // Watch .cursor directory if Cursor is enabled
        if self.config.agents.cursor {
            let cursor_dir = project_path.join(".cursor");
            if cursor_dir.exists() {
                self.watcher
                    .watch(&cursor_dir, RecursiveMode::Recursive)
                    .map_err(|e| Error::Watcher(e.to_string()))?;
                self.watched_paths.insert(cursor_dir, project_id.clone());
                tracing::debug!("Watching .cursor in {}", project_path.display());
            }
        }

        // Watch home directory logs for global agent files
        if let Some(home) = dirs::home_dir() {
            // Claude Code logs
            if self.config.agents.claude {
                let claude_logs = home.join(".claude").join("logs");
                if claude_logs.exists() {
                    self.watcher
                        .watch(&claude_logs, RecursiveMode::NonRecursive)
                        .map_err(|e| Error::Watcher(e.to_string()))?;
                    tracing::debug!("Watching Claude logs at {}", claude_logs.display());
                }
            }
        }

        Ok(())
    }

    /// Run the watcher loop.
    pub async fn run(&mut self) {
        while let Some(result) = self.rx.recv().await {
            match result {
                Ok(event) => {
                    self.handle_event(event).await;
                }
                Err(e) => {
                    tracing::error!("Watch error: {}", e);
                }
            }
        }
    }

    async fn handle_event(&self, event: Event) {
        use notify::EventKind;

        match event.kind {
            EventKind::Create(_) | EventKind::Modify(_) => {
                for path in &event.paths {
                    self.process_file(path).await;
                }
            }
            _ => {}
        }
    }

    async fn process_file(&self, path: &Path) {
        let Some(ext) = path.extension().and_then(|e| e.to_str()) else {
            return;
        };

        // Only process relevant file types
        match ext {
            "jsonl" | "json" | "log" => {}
            _ => return,
        }

        tracing::debug!("File changed: {}", path.display());

        // Determine file type and parse accordingly
        if let Some(file_name) = path.file_name().and_then(|n| n.to_str()) {
            if file_name.contains("conversation") || file_name.contains("chat") {
                self.parse_conversation_log(path).await;
            } else if file_name.contains("mcp") {
                self.parse_mcp_log(path).await;
            }
        }
    }

    async fn parse_conversation_log(&self, path: &Path) {
        // TODO: Parse conversation logs and extract events
        // This will be implemented to detect:
        // - User corrections
        // - Error patterns
        // - Success/failure outcomes
        tracing::debug!("Would parse conversation log: {}", path.display());
    }

    async fn parse_mcp_log(&self, path: &Path) {
        // TODO: Parse MCP tool call logs
        tracing::debug!("Would parse MCP log: {}", path.display());
    }
}
