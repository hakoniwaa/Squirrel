//! MCP server (stdio transport).

use crate::config::Config;
use crate::db::Database;
use crate::error::Error;

/// Run MCP server.
pub async fn run() -> Result<(), Error> {
    tracing::info!("Starting MCP server on stdio...");

    let db_path = Config::global_db_path();
    if let Some(parent) = db_path.parent() {
        std::fs::create_dir_all(parent)?;
    }
    let _db = Database::open(&db_path)?;

    // TODO: Implement MCP server with rmcp
    // For now, just a placeholder
    tracing::info!("MCP server not yet implemented");
    tracing::info!("Waiting for input on stdin...");

    // Keep process alive for testing
    let mut input = String::new();
    loop {
        input.clear();
        if std::io::stdin().read_line(&mut input).is_err() {
            break;
        }
        if input.is_empty() {
            break;
        }

        // Parse JSON-RPC request
        if let Ok(request) = serde_json::from_str::<serde_json::Value>(&input) {
            let method = request["method"].as_str().unwrap_or("");
            let id = &request["id"];

            let response = match method {
                "initialize" => {
                    serde_json::json!({
                        "jsonrpc": "2.0",
                        "id": id,
                        "result": {
                            "protocolVersion": "2024-11-05",
                            "capabilities": {
                                "tools": {}
                            },
                            "serverInfo": {
                                "name": "squirrel",
                                "version": "0.1.0"
                            }
                        }
                    })
                }
                "tools/list" => {
                    serde_json::json!({
                        "jsonrpc": "2.0",
                        "id": id,
                        "result": {
                            "tools": [
                                {
                                    "name": "search_memories",
                                    "description": "Search for relevant memories",
                                    "inputSchema": {
                                        "type": "object",
                                        "properties": {
                                            "query": {
                                                "type": "string",
                                                "description": "Search query"
                                            }
                                        },
                                        "required": ["query"]
                                    }
                                },
                                {
                                    "name": "add_memory",
                                    "description": "Add a new memory",
                                    "inputSchema": {
                                        "type": "object",
                                        "properties": {
                                            "text": {
                                                "type": "string",
                                                "description": "Memory text"
                                            },
                                            "kind": {
                                                "type": "string",
                                                "description": "Memory kind"
                                            }
                                        },
                                        "required": ["text"]
                                    }
                                }
                            ]
                        }
                    })
                }
                _ => {
                    serde_json::json!({
                        "jsonrpc": "2.0",
                        "id": id,
                        "error": {
                            "code": -32601,
                            "message": "Method not found"
                        }
                    })
                }
            };

            println!("{}", serde_json::to_string(&response)?);
        }
    }

    Ok(())
}
