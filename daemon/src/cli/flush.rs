//! Force episode boundary and processing.

use crate::config::Config;
use crate::error::Error;
use crate::ipc;

/// Run flush command.
pub async fn run() -> Result<(), Error> {
    println!("Flushing episode buffer...");

    let config = Config::load()?;
    let socket_path = &config.daemon.socket_path;

    // Try to connect to daemon
    match ipc::send_flush(socket_path).await {
        Ok(()) => {
            println!("Flush request sent to daemon.");
        }
        Err(e) => {
            println!("Could not connect to daemon: {}", e);
            println!("Is the daemon running? Start with: sqrl daemon");
        }
    }

    Ok(())
}
