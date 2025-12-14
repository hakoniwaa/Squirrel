//! Background daemon.

use crate::config::{Config, ProjectsRegistry};
use crate::error::Error;
use crate::watcher::LogWatcher;

/// Run background daemon.
pub async fn run() -> Result<(), Error> {
    let config = Config::load()?;
    tracing::info!("Starting Squirrel daemon...");
    tracing::info!("Socket: {}", config.daemon.socket_path);

    // Load registered projects
    let registry = ProjectsRegistry::load()?;
    tracing::info!("Watching {} projects", registry.projects.len());

    // Create watcher
    let mut watcher = LogWatcher::new(&config)?;

    // Add project paths to watch
    for project in &registry.projects {
        if let Err(e) = watcher.watch_project(&project.root_path) {
            tracing::warn!("Failed to watch {}: {}", project.root_path.display(), e);
        }
    }

    // Start IPC server
    let socket_path = config.daemon.socket_path.clone();
    let ipc_handle = tokio::spawn(async move {
        if let Err(e) = crate::ipc::run_server(&socket_path).await {
            tracing::error!("IPC server error: {}", e);
        }
    });

    // Run watcher loop
    let watcher_handle = tokio::spawn(async move {
        watcher.run().await;
    });

    tracing::info!("Daemon running. Press Ctrl+C to stop.");

    // Wait for shutdown signal
    tokio::select! {
        _ = tokio::signal::ctrl_c() => {
            tracing::info!("Shutting down...");
        }
        _ = ipc_handle => {
            tracing::error!("IPC server stopped unexpectedly");
        }
        _ = watcher_handle => {
            tracing::error!("Watcher stopped unexpectedly");
        }
    }

    Ok(())
}
