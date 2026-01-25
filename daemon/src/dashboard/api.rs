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
        .route("/config/api", get(get_api_config))
        .route("/config/api", post(save_api_config))
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
    match storage::add_user_style(&req.text) {
        Ok(_) => StatusCode::CREATED,
        Err(_) => StatusCode::INTERNAL_SERVER_ERROR,
    }
}

async fn delete_style(Path(id): Path<String>) -> StatusCode {
    match storage::delete_user_style(&id) {
        Ok(true) => StatusCode::NO_CONTENT,
        Ok(false) => StatusCode::NOT_FOUND,
        Err(_) => StatusCode::INTERNAL_SERVER_ERROR,
    }
}

// === Projects ===

#[derive(Serialize)]
struct ProjectResponse {
    id: String,
    path: String,
    memory_count: usize,
}

async fn list_projects() -> Json<Vec<ProjectResponse>> {
    let projects = discover_projects();
    Json(projects)
}

/// Discover projects by scanning common locations for .sqrl directories.
fn discover_projects() -> Vec<ProjectResponse> {
    let mut projects = Vec::new();

    // Check current directory
    if let Ok(cwd) = std::env::current_dir() {
        if let Some(proj) = check_project_dir(&cwd) {
            projects.push(proj);
        }
    }

    // Check home directory common locations
    if let Some(home) = dirs::home_dir() {
        let search_dirs = [
            home.join("projects"),
            home.join("dev"),
            home.join("code"),
            home.join("src"),
            home.join("repos"),
            home.join("workspace"),
        ];

        for dir in search_dirs {
            if dir.exists() {
                if let Ok(entries) = std::fs::read_dir(&dir) {
                    for entry in entries.flatten() {
                        let path = entry.path();
                        if path.is_dir() {
                            if let Some(proj) = check_project_dir(&path) {
                                projects.push(proj);
                            }
                        }
                    }
                }
            }
        }
    }

    projects
}

/// Check if a directory is a Squirrel project and return info.
fn check_project_dir(path: &std::path::Path) -> Option<ProjectResponse> {
    let sqrl_dir = path.join(".sqrl");
    if !sqrl_dir.exists() {
        return None;
    }

    let memory_count = storage::get_project_memories(path)
        .map(|m| m.len())
        .unwrap_or(0);

    let id = path.to_string_lossy().replace('/', "-");
    let path_str = path.to_string_lossy().to_string();

    Some(ProjectResponse {
        id,
        path: path_str,
        memory_count,
    })
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
    #[serde(default)]
    subcategory: String,
    text: String,
}

async fn add_memory(Path(id): Path<String>, Json(req): Json<AddMemoryRequest>) -> StatusCode {
    let project_path = id.replace('-', "/");
    let path = std::path::Path::new(&project_path);

    let subcategory = if req.subcategory.is_empty() {
        "main"
    } else {
        &req.subcategory
    };

    match storage::add_project_memory(path, &req.category, subcategory, &req.text) {
        Ok(_) => StatusCode::CREATED,
        Err(_) => StatusCode::INTERNAL_SERVER_ERROR,
    }
}

async fn delete_memory(Path((id, mid)): Path<(String, String)>) -> StatusCode {
    let project_path = id.replace('-', "/");
    let path = std::path::Path::new(&project_path);

    match storage::delete_project_memory(path, &mid) {
        Ok(true) => StatusCode::NO_CONTENT,
        Ok(false) => StatusCode::NOT_FOUND,
        Err(_) => StatusCode::INTERNAL_SERVER_ERROR,
    }
}

// === API Config ===

#[derive(Serialize)]
struct ApiConfigResponse {
    has_api_key: bool,
    model: Option<String>,
}

async fn get_api_config() -> Json<ApiConfigResponse> {
    let config = storage::get_user_api_config().unwrap_or_default();

    Json(ApiConfigResponse {
        has_api_key: config.openrouter_api_key.is_some(),
        model: config.model,
    })
}

#[derive(Deserialize)]
struct SaveApiConfigRequest {
    openrouter_api_key: Option<String>,
    model: Option<String>,
}

async fn save_api_config(Json(req): Json<SaveApiConfigRequest>) -> StatusCode {
    // Load existing config to preserve fields not being updated
    let mut config = storage::get_user_api_config().unwrap_or_default();

    // Update fields if provided
    if let Some(key) = req.openrouter_api_key {
        if key.is_empty() {
            config.openrouter_api_key = None;
        } else {
            config.openrouter_api_key = Some(key);
        }
    }
    if let Some(model) = req.model {
        if model.is_empty() {
            config.model = None;
        } else {
            config.model = Some(model);
        }
    }

    match storage::save_user_api_config(&config) {
        Ok(_) => StatusCode::OK,
        Err(_) => StatusCode::INTERNAL_SERVER_ERROR,
    }
}
