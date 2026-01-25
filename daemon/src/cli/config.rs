//! Open configuration UI.

use std::process::Command;

use crate::dashboard::DEFAULT_PORT;
use crate::error::Error;

/// Open the config UI in browser.
pub fn open() -> Result<(), Error> {
    let url = format!("http://localhost:{}", DEFAULT_PORT);

    // Check if dashboard is already running
    if !is_dashboard_running() {
        println!("Starting dashboard server...");

        // Get the path to our own executable
        let exe = std::env::current_exe()?;

        // Spawn dashboard in background
        Command::new(&exe)
            .arg("dashboard")
            .stdout(std::process::Stdio::null())
            .stderr(std::process::Stdio::null())
            .spawn()
            .map_err(|e| Error::Ipc(format!("Failed to start dashboard: {}", e)))?;

        // Give it a moment to start
        std::thread::sleep(std::time::Duration::from_millis(500));
    }

    println!("Opening {}", url);

    // Open browser
    open_browser(&url)?;

    Ok(())
}

/// Check if dashboard is already running.
fn is_dashboard_running() -> bool {
    std::net::TcpStream::connect(format!("127.0.0.1:{}", DEFAULT_PORT)).is_ok()
}

/// Open URL in default browser.
fn open_browser(url: &str) -> Result<(), Error> {
    #[cfg(target_os = "macos")]
    {
        Command::new("open")
            .arg(url)
            .spawn()
            .map_err(|e| Error::Ipc(format!("Failed to open browser: {}", e)))?;
    }

    #[cfg(target_os = "linux")]
    {
        // Try xdg-open first, then fallback to common browsers
        if Command::new("xdg-open").arg(url).spawn().is_err() {
            if Command::new("firefox").arg(url).spawn().is_err() {
                if Command::new("chromium").arg(url).spawn().is_err() {
                    Command::new("google-chrome")
                        .arg(url)
                        .spawn()
                        .map_err(|e| Error::Ipc(format!("Failed to open browser: {}", e)))?;
                }
            }
        }
    }

    #[cfg(target_os = "windows")]
    {
        Command::new("cmd")
            .args(["/c", "start", url])
            .spawn()
            .map_err(|e| Error::Ipc(format!("Failed to open browser: {}", e)))?;
    }

    Ok(())
}
