//! Squirrel daemon library.
//!
//! Local-first memory system for AI coding tools.

pub mod cli;
pub mod error;
pub mod ipc;
pub mod mcp;
pub mod storage;
pub mod watcher;

pub use error::Error;
