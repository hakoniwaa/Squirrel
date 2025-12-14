//! Configure settings.

use crate::config::Config;
use crate::error::Error;

/// Run config command.
pub async fn run(key: Option<&str>, value: Option<&str>) -> Result<(), Error> {
    let mut config = Config::load()?;

    match (key, value) {
        // Show all config
        (None, None) => {
            println!("Current configuration:");
            println!();
            println!("[agents]");
            println!("  claude = {}", config.agents.claude);
            println!("  cursor = {}", config.agents.cursor);
            println!("  codex_cli = {}", config.agents.codex_cli);
            println!("  gemini = {}", config.agents.gemini);
            println!("  copilot = {}", config.agents.copilot);
            println!("  windsurf = {}", config.agents.windsurf);
            println!();
            println!("[llm]");
            println!("  strong_model = {}", config.llm.strong_model);
            println!("  fast_model = {}", config.llm.fast_model);
            println!("  embedding_model = {}", config.llm.embedding_model);
            println!();
            println!("[daemon]");
            println!("  socket_path = {}", config.daemon.socket_path);
            println!("  log_level = {}", config.daemon.log_level);
        }

        // Show single key
        (Some(key), None) => {
            let value = get_config_value(&config, key)?;
            println!("{} = {}", key, value);
        }

        // Set key=value
        (Some(key), Some(value)) => {
            set_config_value(&mut config, key, value)?;
            config.save()?;
            println!("Set {} = {}", key, value);
        }

        _ => {
            println!("Usage: sqrl config [KEY] [VALUE]");
        }
    }

    Ok(())
}

fn get_config_value(config: &Config, key: &str) -> Result<String, Error> {
    match key {
        "agents.claude" => Ok(config.agents.claude.to_string()),
        "agents.cursor" => Ok(config.agents.cursor.to_string()),
        "agents.codex_cli" => Ok(config.agents.codex_cli.to_string()),
        "agents.gemini" => Ok(config.agents.gemini.to_string()),
        "agents.copilot" => Ok(config.agents.copilot.to_string()),
        "agents.windsurf" => Ok(config.agents.windsurf.to_string()),
        "llm.strong_model" => Ok(config.llm.strong_model.clone()),
        "llm.fast_model" => Ok(config.llm.fast_model.clone()),
        "llm.embedding_model" => Ok(config.llm.embedding_model.clone()),
        "daemon.socket_path" => Ok(config.daemon.socket_path.clone()),
        "daemon.log_level" => Ok(config.daemon.log_level.clone()),
        _ => Err(Error::InvalidConfig(format!("Unknown key: {}", key))),
    }
}

fn set_config_value(config: &mut Config, key: &str, value: &str) -> Result<(), Error> {
    match key {
        "agents.claude" => config.agents.claude = parse_bool(value)?,
        "agents.cursor" => config.agents.cursor = parse_bool(value)?,
        "agents.codex_cli" => config.agents.codex_cli = parse_bool(value)?,
        "agents.gemini" => config.agents.gemini = parse_bool(value)?,
        "agents.copilot" => config.agents.copilot = parse_bool(value)?,
        "agents.windsurf" => config.agents.windsurf = parse_bool(value)?,
        "llm.strong_model" => config.llm.strong_model = value.to_string(),
        "llm.fast_model" => config.llm.fast_model = value.to_string(),
        "llm.embedding_model" => config.llm.embedding_model = value.to_string(),
        "daemon.socket_path" => config.daemon.socket_path = value.to_string(),
        "daemon.log_level" => config.daemon.log_level = value.to_string(),
        _ => return Err(Error::InvalidConfig(format!("Unknown key: {}", key))),
    }
    Ok(())
}

fn parse_bool(value: &str) -> Result<bool, Error> {
    match value.to_lowercase().as_str() {
        "true" | "1" | "yes" | "on" => Ok(true),
        "false" | "0" | "no" | "off" => Ok(false),
        _ => Err(Error::InvalidConfig(format!(
            "Invalid boolean value: {}",
            value
        ))),
    }
}
