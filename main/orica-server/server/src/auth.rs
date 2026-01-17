use axum::http::HeaderMap;
use std::env;

/// 简易鉴权：校验 Bearer 与环境变量 AUTH_TOKEN（默认 "dummy-token"）
pub fn check_auth(headers: &HeaderMap) -> bool {
    let expected = env::var("AUTH_TOKEN").unwrap_or_else(|_| "dummy-token".to_string());
    match headers.get("authorization").and_then(|h| h.to_str().ok()) {
        Some(v) if v == format!("Bearer {}", expected) => true,
        _ => false,
    }
}
