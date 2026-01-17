use axum::{
    extract::{ws::WebSocketUpgrade, Path},
    response::IntoResponse,
    routing::{get, post},
    Json, Router,
};
use serde::{Deserialize, Serialize};
use std::net::SocketAddr;
use tokio::net::TcpListener;
use tracing::{info, Level};
use uuid::Uuid;

#[derive(Serialize, Deserialize)]
struct LoginRequest {
    username: String,
    password: String,
}

#[derive(Serialize, Deserialize)]
struct LoginResponse {
    token: String,
}

async fn login(Json(payload): Json<LoginRequest>) -> impl IntoResponse {
    // TODO: replace with real JWT auth and EloqKV lookup
    let token = format!("dummy-{}", payload.username);
    Json(LoginResponse { token })
}

async fn list_devices() -> impl IntoResponse {
    // TODO: fetch from EloqKV
    Json(serde_json::json!({"devices":[]}))
}

async fn get_device(Path(mac): Path<String>) -> impl IntoResponse {
    // TODO: fetch device detail
    Json(serde_json::json!({"mac": mac}))
}

async fn websocket_handler(ws: WebSocketUpgrade) -> impl IntoResponse {
    ws.on_upgrade(handle_socket)
}

async fn handle_socket(stream: axum::extract::ws::WebSocket) {
    // TODO: PyO3 call into Python AI logic
    let _ = stream;
}

#[tokio::main]
async fn main() {
    tracing_subscriber::fmt()
        .with_max_level(Level::INFO)
        .with_target(false)
        .init();

    let app = Router::new()
        .route("/api/auth/login", post(login))
        .route("/api/devices", get(list_devices))
        .route("/api/devices/:mac", get(get_device))
        .route("/xiaozhi/v1/", get(websocket_handler))
        .route("/orica/v1/", get(websocket_handler));

    let addr: SocketAddr = "0.0.0.0:8000".parse().unwrap();
    let listener = TcpListener::bind(addr).await.unwrap();
    info!("ORica Axum server listening on {addr}");
    axum::serve(listener, app).await.unwrap();
}
