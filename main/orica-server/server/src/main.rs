use axum::{
    extract::{ws::WebSocketUpgrade, Path, State},
    http::StatusCode,
    response::IntoResponse,
    routing::{get, post},
    Json, Router,
};
use pyo3::prelude::*;
use redis::AsyncCommands;
use serde::{Deserialize, Serialize};
use std::net::SocketAddr;
use tokio::net::TcpListener;
use tracing::{info, Level};

#[derive(Serialize, Deserialize)]
struct LoginRequest {
    username: String,
    password: String,
}

#[derive(Serialize, Deserialize)]
struct LoginResponse {
    token: String,
}

#[derive(Clone)]
struct AppState {
    redis_client: redis::Client,
    key_devices_index: String,
    key_agents_index: String,
    key_config: String,
}

#[derive(Serialize, Deserialize, Default)]
struct Device {
    mac: String,
    user_id: Option<String>,
    agent_id: Option<String>,
    alias: Option<String>,
    firmware_version: Option<String>,
    board: Option<String>,
    last_seen: Option<String>,
}

#[derive(Serialize, Deserialize, Default)]
struct Agent {
    id: String,
    name: Option<String>,
    asr_model_id: Option<String>,
    vad_model_id: Option<String>,
    llm_model_id: Option<String>,
}

#[derive(Serialize, Deserialize, Default)]
struct Config {
    // 根据实际 EloqKV 配置结构扩展
    ws_url: Option<String>,
    http_url: Option<String>,
    extra: Option<serde_json::Value>,
}

async fn login(Json(payload): Json<LoginRequest>) -> impl IntoResponse {
    // TODO: replace with real JWT auth and EloqKV lookup
    let token = format!("dummy-{}", payload.username);
    Json(LoginResponse { token })
}

async fn list_devices(State(state): State<AppState>) -> impl IntoResponse {
    let mut conn = match state.redis_client.get_multiplexed_async_connection().await {
        Ok(c) => c,
        Err(_) => return StatusCode::INTERNAL_SERVER_ERROR.into_response(),
    };
    let macs: Vec<String> = conn
        .smembers(state.key_devices_index.clone())
        .await
        .unwrap_or_default();
    let mut devices: Vec<Device> = Vec::new();
    for mac in macs {
        let key = format!("device:{}", mac);
        let map: redis::RedisResult<std::collections::HashMap<String, String>> =
            conn.hgetall(key).await;
        if let Ok(data) = map {
            devices.push(Device {
                mac: mac.clone(),
                user_id: data.get("user_id").cloned(),
                agent_id: data.get("agent_id").cloned(),
                alias: data.get("alias").cloned(),
                firmware_version: data.get("firmware_version").cloned(),
                board: data.get("board").cloned(),
                last_seen: data.get("last_seen").cloned(),
            });
        }
    }
    Json(serde_json::json!({ "devices": devices })).into_response()
}

async fn get_device(State(state): State<AppState>, Path(mac): Path<String>) -> impl IntoResponse {
    let mut conn = match state.redis_client.get_multiplexed_async_connection().await {
        Ok(c) => c,
        Err(_) => return StatusCode::INTERNAL_SERVER_ERROR.into_response(),
    };
    let key = format!("device:{}", mac);
    let map: redis::RedisResult<std::collections::HashMap<String, String>> =
        conn.hgetall(key).await;
    match map {
        Ok(data) if !data.is_empty() => {
            let device = Device {
                mac: mac.clone(),
                user_id: data.get("user_id").cloned(),
                agent_id: data.get("agent_id").cloned(),
                alias: data.get("alias").cloned(),
                firmware_version: data.get("firmware_version").cloned(),
                board: data.get("board").cloned(),
                last_seen: data.get("last_seen").cloned(),
            };
            Json(device).into_response()
        }
        _ => StatusCode::NOT_FOUND.into_response(),
    }
}

async fn get_agents(State(state): State<AppState>) -> impl IntoResponse {
    let mut conn = match state.redis_client.get_multiplexed_async_connection().await {
        Ok(c) => c,
        Err(_) => return StatusCode::INTERNAL_SERVER_ERROR.into_response(),
    };
    let ids: Vec<String> = conn
        .smembers(state.key_agents_index.clone())
        .await
        .unwrap_or_default();
    let mut agents: Vec<Agent> = Vec::new();
    for id in ids {
        let key = format!("agent:{}", id);
        let map: redis::RedisResult<std::collections::HashMap<String, String>> =
            conn.hgetall(key).await;
        if let Ok(data) = map {
            agents.push(Agent {
                id: id.clone(),
                name: data.get("name").cloned(),
                asr_model_id: data.get("asr_model_id").cloned(),
                vad_model_id: data.get("vad_model_id").cloned(),
                llm_model_id: data.get("llm_model_id").cloned(),
            });
        }
    }
    Json(serde_json::json!({ "agents": agents })).into_response()
}

async fn get_agent(State(state): State<AppState>, Path(id): Path<String>) -> impl IntoResponse {
    let mut conn = match state.redis_client.get_multiplexed_async_connection().await {
        Ok(c) => c,
        Err(_) => return StatusCode::INTERNAL_SERVER_ERROR.into_response(),
    };
    let key = format!("agent:{}", id);
    let map: redis::RedisResult<std::collections::HashMap<String, String>> =
        conn.hgetall(key).await;
    match map {
        Ok(data) if !data.is_empty() => {
            let agent = Agent {
                id: id.clone(),
                name: data.get("name").cloned(),
                asr_model_id: data.get("asr_model_id").cloned(),
                vad_model_id: data.get("vad_model_id").cloned(),
                llm_model_id: data.get("llm_model_id").cloned(),
            };
            Json(agent).into_response()
        }
        _ => StatusCode::NOT_FOUND.into_response(),
    }
}

async fn get_config(State(state): State<AppState>) -> impl IntoResponse {
    let mut conn = match state.redis_client.get_multiplexed_async_connection().await {
        Ok(c) => c,
        Err(_) => return StatusCode::INTERNAL_SERVER_ERROR.into_response(),
    };
    let key = state.key_config.clone();
    let map: redis::RedisResult<std::collections::HashMap<String, String>> =
        conn.hgetall(key).await;
    match map {
        Ok(data) if !data.is_empty() => {
            let cfg = Config {
                ws_url: data.get("ws_url").cloned(),
                http_url: data.get("http_url").cloned(),
                extra: None,
            };
            Json(cfg).into_response()
        }
        _ => StatusCode::NOT_FOUND.into_response(),
    }
}

async fn websocket_handler(ws: WebSocketUpgrade) -> impl IntoResponse {
    ws.on_upgrade(handle_socket)
}

async fn handle_socket(stream: axum::extract::ws::WebSocket) {
    let _ = stream;
    // 示例：调用 Python 打印日志，可替换为实际 AI 处理
    if let Err(err) = call_python_stub() {
        tracing::error!("python stub error: {:?}", err);
    }
}

fn call_python_stub() -> PyResult<()> {
    Python::with_gil(|py| {
        let msg = "ws connection received";
        let builtins = py.import("builtins")?;
        let print = builtins.getattr("print")?;
        print.call1((msg,))?;
        Ok(())
    })
}

#[tokio::main]
async fn main() {
    tracing_subscriber::fmt()
        .with_max_level(Level::INFO)
        .with_target(false)
        .init();

    let redis_url =
        std::env::var("ELOQKV_URL").unwrap_or_else(|_| "redis://127.0.0.1:6379".to_string());
    let redis_client = redis::Client::open(redis_url).expect("invalid redis url");
    let state = AppState {
        redis_client,
        key_devices_index: std::env::var("KEY_DEVICES_INDEX")
            .unwrap_or_else(|_| "devices".to_string()),
        key_agents_index: std::env::var("KEY_AGENTS_INDEX")
            .unwrap_or_else(|_| "agents".to_string()),
        key_config: std::env::var("KEY_CONFIG").unwrap_or_else(|_| "config:global".to_string()),
    };

    let app = Router::new()
        .route("/api/auth/login", post(login))
        .route("/api/devices", get(list_devices))
        .route("/api/devices/:mac", get(get_device))
        .route("/api/agents", get(get_agents))
        .route("/api/agents/:id", get(get_agent))
        .route("/api/config", get(get_config))
        .route("/xiaozhi/v1/", get(websocket_handler))
        .route("/orica/v1/", get(websocket_handler))
        .with_state(state);

    let addr: SocketAddr = "0.0.0.0:8000".parse().unwrap();
    let listener = TcpListener::bind(addr).await.unwrap();
    info!("ORica Axum server listening on {addr}");
    axum::serve(listener, app).await.unwrap();
}
