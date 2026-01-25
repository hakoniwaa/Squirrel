//! Dashboard web server.
//!
//! Serves the configuration UI at http://localhost:9741

mod api;

use std::net::SocketAddr;

use axum::Router;
use tower_http::cors::{Any, CorsLayer};
use tracing::info;

use crate::error::Error;

/// Default dashboard port.
pub const DEFAULT_PORT: u16 = 9741;

/// Start the dashboard server.
pub async fn serve(port: u16) -> Result<(), Error> {
    let app = create_router();

    let addr = SocketAddr::from(([127, 0, 0, 1], port));
    info!("Dashboard listening on http://{}", addr);

    let listener = tokio::net::TcpListener::bind(addr)
        .await
        .map_err(|e| Error::Ipc(format!("Failed to bind to port {}: {}", port, e)))?;

    axum::serve(listener, app)
        .await
        .map_err(|e| Error::Ipc(format!("Server error: {}", e)))?;

    Ok(())
}

/// Create the router with all routes.
fn create_router() -> Router {
    let cors = CorsLayer::new()
        .allow_origin(Any)
        .allow_methods(Any)
        .allow_headers(Any);

    Router::new()
        .nest("/api", api::routes())
        .fallback(serve_index)
        .layer(cors)
}

/// Serve the index.html for SPA routing.
async fn serve_index() -> axum::response::Html<&'static str> {
    axum::response::Html(include_str!("static/index.html"))
}
