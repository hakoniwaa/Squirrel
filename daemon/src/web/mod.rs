//! Web server for Squirrel configuration UI (ARCH-004).

mod api;
mod assets;

use std::net::SocketAddr;

use axum::{routing::get, Router};
use tower_http::cors::{Any, CorsLayer};
use tracing::info;

use crate::error::Error;
use crate::global_config::GlobalConfig;

/// Start the web server.
pub async fn serve(open_browser: bool) -> Result<(), Error> {
    // Ensure global config exists
    GlobalConfig::init()?;
    let config = GlobalConfig::load()?;
    let port = config.ui.port;

    let app = Router::new()
        // API routes
        .route("/api/config", get(api::get_config).post(api::update_config))
        .route("/api/mcps", get(api::list_mcps).post(api::create_mcp))
        .route(
            "/api/mcps/:name",
            get(api::get_mcp)
                .put(api::update_mcp)
                .delete(api::delete_mcp),
        )
        .route(
            "/api/preferences",
            get(api::list_preferences).post(api::create_preference),
        )
        .route(
            "/api/preferences/:id",
            axum::routing::delete(api::delete_preference),
        )
        .route(
            "/api/memories",
            get(api::list_memories).post(api::create_memory),
        )
        .route(
            "/api/memories/:id",
            get(api::get_memory)
                .put(api::update_memory)
                .delete(api::delete_memory),
        )
        // Static assets
        .fallback(assets::serve_static)
        .layer(CorsLayer::new().allow_origin(Any).allow_methods(Any));

    let addr = SocketAddr::from(([127, 0, 0, 1], port));
    info!("Starting web server at http://{}", addr);
    println!("Squirrel config UI: http://localhost:{}", port);

    if open_browser {
        let url = format!("http://localhost:{}", port);
        if let Err(e) = open::that(&url) {
            eprintln!("Could not open browser: {}", e);
        }
    }

    let listener = tokio::net::TcpListener::bind(addr).await?;
    axum::serve(listener, app).await?;

    Ok(())
}
