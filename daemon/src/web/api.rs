//! API endpoints for Squirrel web UI.

use axum::{
    extract::{Path, Query},
    http::StatusCode,
    response::IntoResponse,
    Json,
};
use serde::{Deserialize, Serialize};

use crate::global_config::{GlobalConfig, McpConfig};
use crate::storage::Storage;

/// API response wrapper.
#[derive(Serialize)]
struct ApiResponse<T> {
    success: bool,
    #[serde(skip_serializing_if = "Option::is_none")]
    data: Option<T>,
    #[serde(skip_serializing_if = "Option::is_none")]
    error: Option<String>,
}

impl<T: Serialize> ApiResponse<T> {
    fn ok(data: T) -> Json<Self> {
        Json(Self {
            success: true,
            data: Some(data),
            error: None,
        })
    }
}

impl ApiResponse<()> {
    fn error(msg: impl Into<String>) -> (StatusCode, Json<Self>) {
        (
            StatusCode::BAD_REQUEST,
            Json(Self {
                success: false,
                data: None,
                error: Some(msg.into()),
            }),
        )
    }

    fn not_found(msg: impl Into<String>) -> (StatusCode, Json<Self>) {
        (
            StatusCode::NOT_FOUND,
            Json(Self {
                success: false,
                data: None,
                error: Some(msg.into()),
            }),
        )
    }
}

// === Config endpoints ===

pub async fn get_config() -> impl IntoResponse {
    match GlobalConfig::load() {
        Ok(config) => ApiResponse::ok(config).into_response(),
        Err(e) => ApiResponse::error(e.to_string()).into_response(),
    }
}

pub async fn update_config(Json(config): Json<GlobalConfig>) -> impl IntoResponse {
    match config.save() {
        Ok(()) => ApiResponse::ok(config).into_response(),
        Err(e) => ApiResponse::error(e.to_string()).into_response(),
    }
}

// === MCP endpoints ===

pub async fn list_mcps() -> impl IntoResponse {
    match GlobalConfig::list_mcps() {
        Ok(mcps) => ApiResponse::ok(mcps).into_response(),
        Err(e) => ApiResponse::error(e.to_string()).into_response(),
    }
}

pub async fn get_mcp(Path(name): Path<String>) -> impl IntoResponse {
    match GlobalConfig::get_mcp(&name) {
        Ok(mcp) => ApiResponse::ok(mcp).into_response(),
        Err(e) => ApiResponse::not_found(e.to_string()).into_response(),
    }
}

pub async fn create_mcp(Json(mcp): Json<McpConfig>) -> impl IntoResponse {
    match GlobalConfig::save_mcp(&mcp) {
        Ok(()) => ApiResponse::ok(mcp).into_response(),
        Err(e) => ApiResponse::error(e.to_string()).into_response(),
    }
}

pub async fn update_mcp(
    Path(name): Path<String>,
    Json(mut mcp): Json<McpConfig>,
) -> impl IntoResponse {
    mcp.name = name;
    match GlobalConfig::save_mcp(&mcp) {
        Ok(()) => ApiResponse::ok(mcp).into_response(),
        Err(e) => ApiResponse::error(e.to_string()).into_response(),
    }
}

pub async fn delete_mcp(Path(name): Path<String>) -> impl IntoResponse {
    match GlobalConfig::delete_mcp(&name) {
        Ok(()) => ApiResponse::ok(()).into_response(),
        Err(e) => ApiResponse::error(e.to_string()).into_response(),
    }
}

// === Preferences endpoints (global, ~/.sqrl/memory.db) ===

#[derive(Deserialize)]
pub struct CreatePreferenceRequest {
    content: String,
    #[serde(default)]
    tags: Vec<String>,
}

pub async fn list_preferences() -> impl IntoResponse {
    let db_path = match GlobalConfig::memory_db_path() {
        Ok(p) => p,
        Err(e) => return ApiResponse::error(e.to_string()).into_response(),
    };

    // Ensure parent dir exists
    if let Some(parent) = db_path.parent() {
        if !parent.exists() {
            if let Err(e) = std::fs::create_dir_all(parent) {
                return ApiResponse::error(e.to_string()).into_response();
            }
        }
    }

    match Storage::open(&db_path) {
        Ok(storage) => match storage.list_all_memories() {
            Ok(memories) => {
                // Filter to only preference type
                let prefs: Vec<_> = memories
                    .into_iter()
                    .filter(|m| m.memory_type == "preference")
                    .collect();
                ApiResponse::ok(prefs).into_response()
            }
            Err(e) => ApiResponse::error(e.to_string()).into_response(),
        },
        Err(e) => ApiResponse::error(e.to_string()).into_response(),
    }
}

pub async fn create_preference(Json(req): Json<CreatePreferenceRequest>) -> impl IntoResponse {
    let db_path = match GlobalConfig::memory_db_path() {
        Ok(p) => p,
        Err(e) => return ApiResponse::error(e.to_string()).into_response(),
    };

    // Ensure parent dir exists
    if let Some(parent) = db_path.parent() {
        if !parent.exists() {
            if let Err(e) = std::fs::create_dir_all(parent) {
                return ApiResponse::error(e.to_string()).into_response();
            }
        }
    }

    match Storage::open(&db_path) {
        Ok(storage) => match storage.store_memory("preference", &req.content, &req.tags) {
            Ok(result) => ApiResponse::ok(result).into_response(),
            Err(e) => ApiResponse::error(e.to_string()).into_response(),
        },
        Err(e) => ApiResponse::error(e.to_string()).into_response(),
    }
}

pub async fn delete_preference(Path(id): Path<String>) -> impl IntoResponse {
    let db_path = match GlobalConfig::memory_db_path() {
        Ok(p) => p,
        Err(e) => return ApiResponse::error(e.to_string()).into_response(),
    };

    if !db_path.exists() {
        return ApiResponse::not_found("No preferences database").into_response();
    }

    match Storage::open(&db_path) {
        Ok(storage) => match storage.delete_memory(&id) {
            Ok(()) => ApiResponse::ok(()).into_response(),
            Err(e) => ApiResponse::error(e.to_string()).into_response(),
        },
        Err(e) => ApiResponse::error(e.to_string()).into_response(),
    }
}

// === Memory endpoints (project-specific, .sqrl/memory.db) ===

#[derive(Deserialize)]
pub struct ProjectQuery {
    project: String,
}

#[derive(Deserialize)]
pub struct CreateMemoryRequest {
    memory_type: String,
    content: String,
    #[serde(default)]
    tags: Vec<String>,
}

#[derive(Deserialize)]
pub struct UpdateMemoryRequest {
    #[serde(skip_serializing_if = "Option::is_none")]
    memory_type: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    content: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    tags: Option<Vec<String>>,
}

pub async fn list_memories(Query(query): Query<ProjectQuery>) -> impl IntoResponse {
    let project_path = std::path::PathBuf::from(&query.project);
    let db_path = project_path.join(".sqrl").join("memory.db");

    if !db_path.exists() {
        return ApiResponse::not_found("Project not initialized").into_response();
    }

    match Storage::open(&db_path) {
        Ok(storage) => match storage.list_all_memories() {
            Ok(memories) => ApiResponse::ok(memories).into_response(),
            Err(e) => ApiResponse::error(e.to_string()).into_response(),
        },
        Err(e) => ApiResponse::error(e.to_string()).into_response(),
    }
}

pub async fn get_memory(
    Path(id): Path<String>,
    Query(query): Query<ProjectQuery>,
) -> impl IntoResponse {
    let project_path = std::path::PathBuf::from(&query.project);
    let db_path = project_path.join(".sqrl").join("memory.db");

    if !db_path.exists() {
        return ApiResponse::not_found("Project not initialized").into_response();
    }

    match Storage::open(&db_path) {
        Ok(storage) => match storage.get_memory(&id) {
            Ok(Some(memory)) => ApiResponse::ok(memory).into_response(),
            Ok(None) => ApiResponse::not_found("Memory not found").into_response(),
            Err(e) => ApiResponse::error(e.to_string()).into_response(),
        },
        Err(e) => ApiResponse::error(e.to_string()).into_response(),
    }
}

pub async fn create_memory(
    Query(query): Query<ProjectQuery>,
    Json(req): Json<CreateMemoryRequest>,
) -> impl IntoResponse {
    let project_path = std::path::PathBuf::from(&query.project);
    let db_path = project_path.join(".sqrl").join("memory.db");

    if !db_path.exists() {
        return ApiResponse::not_found("Project not initialized").into_response();
    }

    match Storage::open(&db_path) {
        Ok(storage) => match storage.store_memory(&req.memory_type, &req.content, &req.tags) {
            Ok(result) => ApiResponse::ok(result).into_response(),
            Err(e) => ApiResponse::error(e.to_string()).into_response(),
        },
        Err(e) => ApiResponse::error(e.to_string()).into_response(),
    }
}

pub async fn update_memory(
    Path(id): Path<String>,
    Query(query): Query<ProjectQuery>,
    Json(req): Json<UpdateMemoryRequest>,
) -> impl IntoResponse {
    let project_path = std::path::PathBuf::from(&query.project);
    let db_path = project_path.join(".sqrl").join("memory.db");

    if !db_path.exists() {
        return ApiResponse::not_found("Project not initialized").into_response();
    }

    match Storage::open(&db_path) {
        Ok(storage) => {
            match storage.update_memory(
                &id,
                req.memory_type.as_deref(),
                req.content.as_deref(),
                req.tags.as_deref(),
            ) {
                Ok(()) => ApiResponse::ok(()).into_response(),
                Err(e) => ApiResponse::error(e.to_string()).into_response(),
            }
        }
        Err(e) => ApiResponse::error(e.to_string()).into_response(),
    }
}

pub async fn delete_memory(
    Path(id): Path<String>,
    Query(query): Query<ProjectQuery>,
) -> impl IntoResponse {
    let project_path = std::path::PathBuf::from(&query.project);
    let db_path = project_path.join(".sqrl").join("memory.db");

    if !db_path.exists() {
        return ApiResponse::not_found("Project not initialized").into_response();
    }

    match Storage::open(&db_path) {
        Ok(storage) => match storage.delete_memory(&id) {
            Ok(()) => ApiResponse::ok(()).into_response(),
            Err(e) => ApiResponse::error(e.to_string()).into_response(),
        },
        Err(e) => ApiResponse::error(e.to_string()).into_response(),
    }
}
