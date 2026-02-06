//! Global configuration (CONFIG-001).
//!
//! Handles loading and saving `~/.sqrl/config.yaml` and MCP configs.

use std::fs;
use std::path::PathBuf;

use serde::{Deserialize, Serialize};

use crate::error::Error;

/// Global configuration stored in `~/.sqrl/config.yaml`.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GlobalConfig {
    /// CLI tools enabled (applied to all projects).
    #[serde(default)]
    pub tools: GlobalToolsConfig,

    /// Enabled MCP names (from uploaded config).
    #[serde(default)]
    pub mcps: Vec<String>,

    /// Web UI settings.
    #[serde(default)]
    pub ui: UiConfig,
}

/// CLI tools configuration.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GlobalToolsConfig {
    #[serde(default = "default_true")]
    pub claude_code: bool,
    #[serde(default = "default_true")]
    pub git: bool,
    #[serde(default)]
    pub cursor: bool,
    #[serde(default)]
    pub codex: bool,
}

/// Web UI settings.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct UiConfig {
    #[serde(default = "default_port")]
    pub port: u16,
    #[serde(default = "default_true")]
    pub open_browser: bool,
}

/// MCP configuration file (MCP-CONFIG-001).
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct McpConfig {
    pub name: String,
    pub command: String,
    #[serde(default)]
    pub args: Vec<String>,
    #[serde(default)]
    pub env: std::collections::HashMap<String, String>,
    #[serde(default = "default_scope")]
    pub scope: String,
}

fn default_true() -> bool {
    true
}

fn default_port() -> u16 {
    3333
}

fn default_scope() -> String {
    "project".to_string()
}

impl Default for GlobalToolsConfig {
    fn default() -> Self {
        Self {
            claude_code: true,
            git: true,
            cursor: false,
            codex: false,
        }
    }
}

impl Default for UiConfig {
    fn default() -> Self {
        Self {
            port: 3333,
            open_browser: true,
        }
    }
}

impl Default for GlobalConfig {
    fn default() -> Self {
        Self {
            tools: GlobalToolsConfig::default(),
            mcps: vec![],
            ui: UiConfig::default(),
        }
    }
}

impl GlobalConfig {
    /// Get the global sqrl directory path.
    pub fn dir() -> Result<PathBuf, Error> {
        dirs::home_dir()
            .map(|h| h.join(".sqrl"))
            .ok_or(Error::NoHomeDir)
    }

    /// Get the global config file path.
    pub fn path() -> Result<PathBuf, Error> {
        Ok(Self::dir()?.join("config.yaml"))
    }

    /// Get the MCPs directory path.
    pub fn mcps_dir() -> Result<PathBuf, Error> {
        Ok(Self::dir()?.join("mcps"))
    }

    /// Get the global memory database path.
    pub fn memory_db_path() -> Result<PathBuf, Error> {
        Ok(Self::dir()?.join("memory.db"))
    }

    /// Initialize global config directory if not exists.
    pub fn init() -> Result<(), Error> {
        let dir = Self::dir()?;
        if !dir.exists() {
            fs::create_dir_all(&dir)?;
        }

        let mcps_dir = Self::mcps_dir()?;
        if !mcps_dir.exists() {
            fs::create_dir_all(&mcps_dir)?;
        }

        let config_path = Self::path()?;
        if !config_path.exists() {
            let config = GlobalConfig::default();
            config.save()?;
        }

        // Create default squirrel MCP config
        let squirrel_mcp = mcps_dir.join("squirrel.json");
        if !squirrel_mcp.exists() {
            let mcp = McpConfig {
                name: "squirrel".to_string(),
                command: "sqrl".to_string(),
                args: vec!["mcp-serve".to_string()],
                env: std::collections::HashMap::new(),
                scope: "project".to_string(),
            };
            let content = serde_json::to_string_pretty(&mcp)?;
            fs::write(&squirrel_mcp, content)?;
        }

        Ok(())
    }

    /// Check if global config exists.
    pub fn exists() -> bool {
        Self::path().map(|p| p.exists()).unwrap_or(false)
    }

    /// Load global config.
    pub fn load() -> Result<Self, Error> {
        let path = Self::path()?;
        if !path.exists() {
            return Err(Error::GlobalConfigNotFound);
        }
        let content = fs::read_to_string(&path)?;
        let config: GlobalConfig =
            serde_yaml::from_str(&content).map_err(|e| Error::ConfigParse(e.to_string()))?;
        Ok(config)
    }

    /// Save global config.
    pub fn save(&self) -> Result<(), Error> {
        let path = Self::path()?;
        let content = serde_yaml::to_string(self).map_err(|e| Error::ConfigParse(e.to_string()))?;
        let with_header = format!("# Squirrel global configuration\n\n{}", content);
        fs::write(&path, with_header)?;
        Ok(())
    }

    /// List all MCP configs.
    pub fn list_mcps() -> Result<Vec<McpConfig>, Error> {
        let mcps_dir = Self::mcps_dir()?;
        if !mcps_dir.exists() {
            return Ok(vec![]);
        }

        let mut mcps = vec![];
        for entry in fs::read_dir(&mcps_dir)? {
            let entry = entry?;
            let path = entry.path();
            if path.extension().map(|e| e == "json").unwrap_or(false) {
                let content = fs::read_to_string(&path)?;
                let mcp: McpConfig = serde_json::from_str(&content)?;
                mcps.push(mcp);
            }
        }
        Ok(mcps)
    }

    /// Get a specific MCP config by name.
    pub fn get_mcp(name: &str) -> Result<McpConfig, Error> {
        let path = Self::mcps_dir()?.join(format!("{}.json", name));
        if !path.exists() {
            return Err(Error::McpNotFound(name.to_string()));
        }
        let content = fs::read_to_string(&path)?;
        let mcp: McpConfig = serde_json::from_str(&content)?;
        Ok(mcp)
    }

    /// Save an MCP config.
    pub fn save_mcp(mcp: &McpConfig) -> Result<(), Error> {
        let path = Self::mcps_dir()?.join(format!("{}.json", mcp.name));
        let content = serde_json::to_string_pretty(mcp)?;
        fs::write(&path, content)?;
        Ok(())
    }

    /// Delete an MCP config.
    pub fn delete_mcp(name: &str) -> Result<(), Error> {
        let path = Self::mcps_dir()?.join(format!("{}.json", name));
        if path.exists() {
            fs::remove_file(&path)?;
        }
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_default_config() {
        let config = GlobalConfig::default();
        assert!(config.tools.claude_code);
        assert!(config.tools.git);
        assert!(!config.tools.cursor);
        assert_eq!(config.ui.port, 3333);
        assert!(config.ui.open_browser);
    }
}
