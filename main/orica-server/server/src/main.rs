use axum::{
    extract::{ws::WebSocketUpgrade, Path, State},
    http::StatusCode,
    http::HeaderMap,
    response::IntoResponse,
    routing::{get, post},
    Json, Router,
};
use pyo3::prelude::*;
use redis::AsyncCommands;
use serde::{Deserialize, Serialize};
use std::net::SocketAddr;
use tokio::net::TcpListener;
use tracing::{error, info, Level};

mod auth;
use auth::check_auth;

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
    tts_model_id: Option<String>,
}

#[derive(Serialize, Deserialize, Default)]
struct Config {
    ws_url: Option<String>,
    http_url: Option<String>,
    tts_model_id: Option<String>,
    asr_model_id: Option<String>,
    llm_model_id: Option<String>,
    extra: Option<serde_json::Value>,
}

async fn login(Json(payload): Json<LoginRequest>) -> impl IntoResponse {
    // TODO: replace with real JWT auth and EloqKV lookup
    let token = format!("dummy-{}", payload.username);
    Json(LoginResponse { token })
}

async fn list_devices(headers: HeaderMap, State(state): State<AppState>) -> impl IntoResponse {
    if !check_auth(&headers) {
        return StatusCode::UNAUTHORIZED.into_response();
    }
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
        } else {
            error!("device key missing for mac {}", mac);
        }
    }
    Json(serde_json::json!({ "devices": devices })).into_response()
}

async fn get_device(
    headers: HeaderMap,
    State(state): State<AppState>,
    Path(mac): Path<String>,
) -> impl IntoResponse {
    if !check_auth(&headers) {
        return StatusCode::UNAUTHORIZED.into_response();
    }
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
        _ => {
            error!("device not found: {}", mac);
            StatusCode::NOT_FOUND.into_response()
        }
    }
}

async fn get_agents(headers: HeaderMap, State(state): State<AppState>) -> impl IntoResponse {
    if !check_auth(&headers) {
        return StatusCode::UNAUTHORIZED.into_response();
    }
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
                tts_model_id: data.get("tts_model_id").cloned(),
            });
        }
    }
    Json(serde_json::json!({ "agents": agents })).into_response()
}

async fn get_agent(
    headers: HeaderMap,
    State(state): State<AppState>,
    Path(id): Path<String>,
) -> impl IntoResponse {
    if !check_auth(&headers) {
        return StatusCode::UNAUTHORIZED.into_response();
    }
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
                tts_model_id: data.get("tts_model_id").cloned(),
            };
            Json(agent).into_response()
        }
        _ => {
            error!("agent not found: {}", id);
            StatusCode::NOT_FOUND.into_response()
        }
    }
}

async fn get_config(headers: HeaderMap, State(state): State<AppState>) -> impl IntoResponse {
    if !check_auth(&headers) {
        return StatusCode::UNAUTHORIZED.into_response();
    }
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
                tts_model_id: data.get("tts_model_id").cloned(),
                asr_model_id: data.get("asr_model_id").cloned(),
                llm_model_id: data.get("llm_model_id").cloned(),
                extra: None,
            };
            Json(cfg).into_response()
        }
        _ => {
            error!("config not found");
            StatusCode::NOT_FOUND.into_response()
        }
    }
}

async fn websocket_handler(ws: WebSocketUpgrade) -> impl IntoResponse {
    ws.on_upgrade(handle_socket)
}

async fn handle_socket(mut stream: axum::extract::ws::WebSocket) {
    while let Some(Ok(msg)) = stream.recv().await {
        match msg {
            axum::extract::ws::Message::Text(text) => {
                let result = call_python_text(&text);
                if let Err(err) = result {
                    error!("python text error: {:?}", err);
                } else if let Ok(output) = result {
                    if stream
                        .send(axum::extract::ws::Message::Text(output.unwrap_or(text)))
                        .await
                        .is_err()
                    {
                        break;
                    }
                }
            }
            axum::extract::ws::Message::Binary(bin) => {
                if let Err(err) = call_python_binary(&bin) {
                    error!("python binary error: {:?}", err);
                }
            }
            axum::extract::ws::Message::Close(_) => break,
            _ => {}
        }
    }
}

fn call_python_text(text: &str) -> PyResult<Option<String>> {
    Python::with_gil(|py| {
        let module = PyModule::import_bound(py, "py_ai_handler")?;
        let func = module.getattr("handle_text")?;
        let res = func.call1((text,))?;
        if res.is_none() {
            Ok(None)
        } else {
            Ok(Some(res.extract::<String>()?))
        }
    })
}

fn call_python_binary(bin: &[u8]) -> PyResult<()> {
    Python::with_gil(|py| {
        let module = PyModule::import_bound(py, "py_ai_handler")?;
        let func = module.getattr("handle_binary")?;
        func.call1((bin,))?;
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
