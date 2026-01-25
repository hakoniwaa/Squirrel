//! Dashboard API handlers.

use axum::{
    extract::Path,
    http::StatusCode,
    routing::{delete, get, post},
    Json, Router,
};
use serde::{Deserialize, Serialize};

use crate::cli::service;
use crate::storage;

/// API routes.
pub fn routes() -> Router {
    Router::new()
        .route("/status", get(get_status))
        .route("/styles", get(list_styles))
        .route("/styles", post(add_style))
        .route("/styles/{id}", delete(delete_style))
        .route("/projects", get(list_projects))
        .route("/projects/{id}/memories", get(list_memories))
        .route("/projects/{id}/memories", post(add_memory))
        .route("/projects/{id}/memories/{mid}", delete(delete_memory))
}

// === Status ===

#[derive(Serialize)]
struct StatusResponse {
    daemon_running: bool,
    user_styles_count: usize,
}

async fn get_status() -> Json<StatusResponse> {
    let daemon_running = service::is_running().unwrap_or(false);
    let user_styles_count = storage::get_user_styles().map(|s| s.len()).unwrap_or(0);

    Json(StatusResponse {
        daemon_running,
        user_styles_count,
    })
}

// === User Styles ===

#[derive(Serialize)]
struct StyleResponse {
    id: String,
    text: String,
    use_count: i64,
}

async fn list_styles() -> Json<Vec<StyleResponse>> {
    let styles = storage::get_user_styles().unwrap_or_default();

    Json(
        styles
            .into_iter()
            .map(|s| StyleResponse {
                id: s.id,
                text: s.text,
                use_count: s.use_count,
            })
            .collect(),
    )
}

#[derive(Deserialize)]
struct AddStyleRequest {
    text: String,
}

async fn add_style(Json(req): Json<AddStyleRequest>) -> StatusCode {
    // TODO: Implement add style to storage
    let _ = req.text;
    StatusCode::CREATED
}

async fn delete_style(Path(id): Path<String>) -> StatusCode {
    // TODO: Implement delete style from storage
    let _ = id;
    StatusCode::NO_CONTENT
}

// === Projects ===

#[derive(Serialize)]
struct ProjectResponse {
    id: String,
    path: String,
    memory_count: usize,
}

async fn list_projects() -> Json<Vec<ProjectResponse>> {
    // TODO: Implement project listing (scan for .sqrl directories)
    Json(vec![])
}

// === Project Memories ===

#[derive(Serialize)]
struct MemoryResponse {
    id: String,
    category: String,
    subcategory: String,
    text: String,
    use_count: i64,
}

async fn list_memories(Path(id): Path<String>) -> Json<Vec<MemoryResponse>> {
    // Project ID is the path with slashes replaced by dashes
    // e.g., "-home-user-projects-myapp" -> "/home/user/projects/myapp"
    let project_path = id.replace('-', "/");
    let path = std::path::Path::new(&project_path);

    let memories = storage::get_project_memories(path).unwrap_or_default();

    Json(
        memories
            .into_iter()
            .map(|m| MemoryResponse {
                id: m.id,
                category: m.category,
                subcategory: m.subcategory,
                text: m.text,
                use_count: m.use_count,
            })
            .collect(),
    )
}

#[derive(Deserialize)]
struct AddMemoryRequest {
    category: String,
    text: String,
}

async fn add_memory(Path(id): Path<String>, Json(req): Json<AddMemoryRequest>) -> StatusCode {
    // TODO: Implement add memory to storage
    let _ = (id, req);
    StatusCode::CREATED
}

async fn delete_memory(Path((id, mid)): Path<(String, String)>) -> StatusCode {
    // TODO: Implement delete memory from storage
    let _ = (id, mid);
    StatusCode::NO_CONTENT
}
