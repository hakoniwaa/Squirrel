//! File watcher for Claude Code logs.

use std::path::PathBuf;
use std::sync::mpsc;
use std::time::Duration;

use notify::{Config, EventKind, PollWatcher, RecursiveMode, Watcher};
use tracing::{debug, info, warn};

use crate::Error;

/// Poll interval for watching file changes (WSL/9p filesystems don't support inotify).
const POLL_INTERVAL_SECS: u64 = 2;

/// Events emitted by the file watcher.
#[derive(Debug, Clone)]
pub enum WatchEvent {
    /// A log file was modified.
    Modified(PathBuf),
    /// A new log file was created.
    Created(PathBuf),
}

/// Watches ~/.claude/projects for log file changes.
/// Uses poll-based watching for compatibility with WSL/9p filesystems.
pub struct FileWatcher {
    watcher: PollWatcher,
    rx: mpsc::Receiver<WatchEvent>,
    claude_dir: PathBuf,
}

impl FileWatcher {
    /// Create a new file watcher.
    ///
    /// Uses poll-based watching for compatibility with WSL/9p filesystems
    /// where inotify doesn't work.
    pub fn new() -> Result<Self, Error> {
        let home = dirs::home_dir().ok_or(Error::HomeDirNotFound)?;
        let claude_dir = home.join(".claude").join("projects");

        if !claude_dir.exists() {
            info!(path = %claude_dir.display(), "Claude projects directory does not exist yet");
        }

        let (tx, rx) = mpsc::channel();

        // Use PollWatcher for WSL/9p filesystem compatibility
        // inotify doesn't work on 9p mounted filesystems (Windows drives in WSL)
        let config = Config::default().with_poll_interval(Duration::from_secs(POLL_INTERVAL_SECS));

        let watcher = PollWatcher::new(
            move |res: Result<notify::Event, notify::Error>| {
                match res {
                    Ok(event) => {
                        for path in event.paths {
                            // Only process .jsonl files
                            if path.extension().is_some_and(|ext| ext == "jsonl") {
                                let watch_event = match event.kind {
                                    EventKind::Create(_) => Some(WatchEvent::Created(path.clone())),
                                    EventKind::Modify(_) => {
                                        Some(WatchEvent::Modified(path.clone()))
                                    }
                                    _ => None,
                                };

                                if let Some(evt) = watch_event {
                                    debug!(?evt, "File event");
                                    if tx.send(evt).is_err() {
                                        warn!("Receiver dropped, stopping watcher");
                                        return;
                                    }
                                }
                            }
                        }
                    }
                    Err(e) => {
                        warn!(error = %e, "Watch error");
                    }
                }
            },
            config,
        )?;

        Ok(Self {
            watcher,
            rx,
            claude_dir,
        })
    }

    /// Start watching for file changes.
    pub fn start(&mut self) -> Result<(), Error> {
        if self.claude_dir.exists() {
            self.watcher
                .watch(&self.claude_dir, RecursiveMode::Recursive)?;
            info!(path = %self.claude_dir.display(), "Watching for log changes");
        } else {
            // Watch parent directory so we catch when .claude/projects is created
            let parent = self.claude_dir.parent().unwrap_or(&self.claude_dir);
            if parent.exists() {
                self.watcher.watch(parent, RecursiveMode::Recursive)?;
                info!(path = %parent.display(), "Watching parent for .claude creation");
            } else {
                warn!("Claude directory parent does not exist, will retry on next event");
            }
        }
        Ok(())
    }

    /// Receive the next watch event, blocking.
    #[allow(dead_code)]
    pub fn recv(&self) -> Option<WatchEvent> {
        self.rx.recv().ok()
    }

    /// Try to receive a watch event without blocking.
    pub fn try_recv(&self) -> Option<WatchEvent> {
        self.rx.try_recv().ok()
    }

    /// Get the Claude projects directory path.
    #[allow(dead_code)]
    pub fn claude_dir(&self) -> &PathBuf {
        &self.claude_dir
    }
}
