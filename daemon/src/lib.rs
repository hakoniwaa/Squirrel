//! Squirrel library.
//!
//! Local-first memory system for AI coding tools.
//! Single binary. No daemon. No AI. Just storage + git hooks.

pub mod cli;
pub mod config;
pub mod error;
pub mod mcp;
pub mod storage;

pub use config::Config;
pub use error::Error;
