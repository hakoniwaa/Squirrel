//! Squirrel - local-first memory system for AI coding tools.
//!
//! Single binary. No daemon. No AI. Just storage + git hooks.

use clap::{Parser, Subcommand};
use tracing_subscriber::{fmt, prelude::*, EnvFilter};

mod cli;
mod config;
mod error;
mod mcp;
mod storage;

pub use error::Error;

#[derive(Parser)]
#[command(name = "sqrl")]
#[command(about = "Squirrel - local-first memory system for AI coding tools")]
#[command(version)]
struct Cli {
    #[command(subcommand)]
    command: Option<Commands>,
}

#[derive(Subcommand)]
enum Commands {
    /// Initialize Squirrel for this project
    Init,

    /// Remove all Squirrel data from this project
    Goaway {
        /// Skip confirmation prompt
        #[arg(long, short)]
        force: bool,
    },

    /// Show Squirrel status
    Status,

    /// Start MCP server (called by AI tool config, not user)
    #[command(name = "mcp-serve")]
    McpServe,

    /// Internal commands (used by git hooks)
    #[command(hide = true, name = "_internal")]
    Internal {
        #[command(subcommand)]
        cmd: InternalCommands,
    },
}

#[derive(Subcommand)]
enum InternalCommands {
    /// Record doc debt after commit (post-commit hook)
    #[command(name = "docguard-record")]
    DocguardRecord,

    /// Check doc debt before push (pre-push hook)
    #[command(name = "docguard-check")]
    DocguardCheck,
}

fn main() -> Result<(), Error> {
    // Initialize logging
    tracing_subscriber::registry()
        .with(fmt::layer())
        .with(EnvFilter::from_default_env().add_directive("sqrl=info".parse().unwrap()))
        .init();

    let cli = Cli::parse();

    match cli.command {
        None => {
            use clap::CommandFactory;
            Cli::command().print_help().unwrap();
            println!();
        }
        Some(Commands::Init) => {
            cli::init::run()?;
        }
        Some(Commands::Goaway { force }) => {
            cli::goaway::run(force)?;
        }
        Some(Commands::Status) => {
            let exit_code = cli::status::run()?;
            if exit_code != 0 {
                std::process::exit(exit_code);
            }
        }
        Some(Commands::McpServe) => {
            mcp::run()?;
        }
        Some(Commands::Internal { cmd }) => match cmd {
            InternalCommands::DocguardRecord => {
                cli::internal::docguard_record()?;
            }
            InternalCommands::DocguardCheck => {
                if !cli::internal::docguard_check()? {
                    std::process::exit(1);
                }
            }
        },
    }

    Ok(())
}
