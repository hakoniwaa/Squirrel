//! MCP server for AI tools.
//!
//! MCP-001: squirrel_store_memory
//! MCP-002: squirrel_get_memory

use std::io::{BufRead, Write};
use std::path::Path;

use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use tracing::{debug, error, info};

use crate::error::Error;
use crate::storage;

const PROTOCOL_VERSION: &str = "2024-11-05";
const SERVER_NAME: &str = "squirrel";
const SERVER_VERSION: &str = env!("CARGO_PKG_VERSION");

#[derive(Debug, Deserialize)]
struct JsonRpcRequest {
    #[allow(dead_code)]
    jsonrpc: String,
    method: String,
    #[serde(default)]
    params: Value,
    id: Option<Value>,
}

#[derive(Debug, Serialize)]
struct JsonRpcResponse {
    jsonrpc: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    result: Option<Value>,
    #[serde(skip_serializing_if = "Option::is_none")]
    error: Option<JsonRpcError>,
    id: Value,
}

#[derive(Debug, Serialize)]
struct JsonRpcError {
    code: i32,
    message: String,
}

impl JsonRpcResponse {
    fn success(id: Value, result: Value) -> Self {
        Self {
            jsonrpc: "2.0".to_string(),
            result: Some(result),
            error: None,
            id,
        }
    }

    fn error(id: Value, code: i32, message: String) -> Self {
        Self {
            jsonrpc: "2.0".to_string(),
            result: None,
            error: Some(JsonRpcError { code, message }),
            id,
        }
    }
}

/// MCP tool definitions.
fn get_tools() -> Value {
    json!({
        "tools": [
            {
                "name": "squirrel_store_memory",
                "description": "Store a behavioral correction. Use when the user corrects you or you learn a project rule.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "content": {
                            "type": "string",
                            "description": "An actionable instruction: 'Do X', 'Don't do Y', or 'When Z, do W' (1-2 sentences)"
                        },
                        "memory_type": {
                            "type": "string",
                            "enum": ["preference", "project"],
                            "description": "Type: preference (global user preference), project (project-specific rule)"
                        },
                        "tags": {
                            "type": "array",
                            "items": { "type": "string" },
                            "description": "Tags for organization"
                        }
                    },
                    "required": ["content", "memory_type"]
                }
            },
            {
                "name": "squirrel_get_memory",
                "description": "Get behavioral corrections from Squirrel. Call at session start or before making choices.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "memory_type": {
                            "type": "string",
                            "enum": ["preference", "project"],
                            "description": "Filter by type. Omit to get all."
                        },
                        "tags": {
                            "type": "array",
                            "items": { "type": "string" },
                            "description": "Filter by tags. Omit to get all."
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Max memories to return. Default 50."
                        }
                    },
                    "required": []
                }
            }
        ]
    })
}

/// Get project root from MCP params, falling back to cwd.
fn get_project_root(params: &Value) -> Result<std::path::PathBuf, Error> {
    // Try to get from arguments
    if let Some(root) = params
        .get("arguments")
        .and_then(|a| a.get("project_root"))
        .and_then(|p| p.as_str())
    {
        let path = Path::new(root);
        if path.exists() {
            return Ok(path.to_path_buf());
        }
    }

    // Fall back to current working directory
    std::env::current_dir().map_err(Error::Io)
}

/// Handle squirrel_store_memory.
fn handle_store_memory(params: &Value) -> Result<Value, Error> {
    let args = params.get("arguments").unwrap_or(params);

    let content = args
        .get("content")
        .and_then(|c| c.as_str())
        .ok_or_else(|| Error::Mcp("Missing 'content' parameter".to_string()))?;

    let memory_type = args
        .get("memory_type")
        .and_then(|t| t.as_str())
        .ok_or_else(|| Error::Mcp("Missing 'memory_type' parameter".to_string()))?;

    let tags: Vec<String> = args
        .get("tags")
        .and_then(|t| t.as_array())
        .map(|arr| {
            arr.iter()
                .filter_map(|v| v.as_str().map(|s| s.to_string()))
                .collect()
        })
        .unwrap_or_default();

    let project_root = get_project_root(params)?;
    let (_id, deduplicated, use_count) =
        storage::store_memory(&project_root, memory_type, content, &tags)?;

    let msg = if deduplicated {
        format!("Memory reinforced (use_count: {}): {}", use_count, content)
    } else {
        format!("Memory stored: {}", content)
    };

    Ok(json!({
        "content": [{
            "type": "text",
            "text": msg
        }]
    }))
}

/// Handle squirrel_get_memory.
fn handle_get_memory(params: &Value) -> Result<Value, Error> {
    let args = params.get("arguments").unwrap_or(params);

    let memory_type = args.get("memory_type").and_then(|t| t.as_str());

    let tags: Option<Vec<String>> = args.get("tags").and_then(|t| t.as_array()).map(|arr| {
        arr.iter()
            .filter_map(|v| v.as_str().map(|s| s.to_string()))
            .collect()
    });

    let limit = args.get("limit").and_then(|l| l.as_i64());

    let project_root = get_project_root(params)?;
    let markdown =
        storage::format_memories_as_markdown(&project_root, memory_type, tags.as_deref(), limit)?;

    Ok(json!({
        "content": [{
            "type": "text",
            "text": markdown
        }]
    }))
}

/// Handle incoming MCP request.
fn handle_request(request: &JsonRpcRequest) -> JsonRpcResponse {
    let id = request.id.clone().unwrap_or(Value::Null);

    match request.method.as_str() {
        "initialize" => {
            info!("MCP initialize");
            JsonRpcResponse::success(
                id,
                json!({
                    "protocolVersion": PROTOCOL_VERSION,
                    "capabilities": {
                        "tools": {}
                    },
                    "serverInfo": {
                        "name": SERVER_NAME,
                        "version": SERVER_VERSION
                    }
                }),
            )
        }

        "notifications/initialized" => {
            debug!("MCP initialized notification");
            JsonRpcResponse::success(id, json!({}))
        }

        "tools/list" => {
            debug!("MCP tools/list");
            JsonRpcResponse::success(id, get_tools())
        }

        "tools/call" => {
            let tool_name = request
                .params
                .get("name")
                .and_then(|n| n.as_str())
                .unwrap_or("");

            debug!(tool = tool_name, "MCP tools/call");

            match tool_name {
                "squirrel_store_memory" => match handle_store_memory(&request.params) {
                    Ok(result) => JsonRpcResponse::success(id, result),
                    Err(e) => JsonRpcResponse::error(id, -32000, e.to_string()),
                },
                "squirrel_get_memory" => match handle_get_memory(&request.params) {
                    Ok(result) => JsonRpcResponse::success(id, result),
                    Err(e) => JsonRpcResponse::error(id, -32000, e.to_string()),
                },
                _ => JsonRpcResponse::error(id, -32601, format!("Unknown tool: {}", tool_name)),
            }
        }

        _ => {
            debug!(method = request.method, "Unknown MCP method");
            JsonRpcResponse::error(id, -32601, format!("Method not found: {}", request.method))
        }
    }
}

/// Run the MCP server (stdio mode).
pub fn run() -> Result<(), Error> {
    info!("Starting MCP server");

    let stdin = std::io::stdin();
    let mut stdout = std::io::stdout();

    for line in stdin.lock().lines() {
        let line = line?;
        if line.is_empty() {
            continue;
        }

        debug!(request = %line, "MCP request");

        let request: JsonRpcRequest = match serde_json::from_str(&line) {
            Ok(req) => req,
            Err(e) => {
                error!(error = %e, "Failed to parse MCP request");
                let response =
                    JsonRpcResponse::error(Value::Null, -32700, format!("Parse error: {}", e));
                let response_str = serde_json::to_string(&response)?;
                writeln!(stdout, "{}", response_str)?;
                stdout.flush()?;
                continue;
            }
        };

        // Skip notifications (no id)
        if request.id.is_none() && request.method.starts_with("notifications/") {
            debug!(method = request.method, "Skipping notification");
            continue;
        }

        let response = handle_request(&request);
        let response_str = serde_json::to_string(&response)?;

        debug!(response = %response_str, "MCP response");

        writeln!(stdout, "{}", response_str)?;
        stdout.flush()?;
    }

    info!("MCP server stopped");
    Ok(())
}
