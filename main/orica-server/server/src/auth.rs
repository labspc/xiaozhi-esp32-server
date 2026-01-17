use axum::http::HeaderMap;
use std::env;
use crate::jwt_stub::validate_token;

/// 简易鉴权：校验 Bearer 与环境变量 AUTH_TOKEN（默认 "dummy-token"）
pub fn check_auth(headers: &HeaderMap) -> bool {
    let expected = env::var("AUTH_TOKEN").unwrap_or_else(|_| "dummy-token".to_string());
    match headers.get("authorization").and_then(|h| h.to_str().ok()) {
        Some(v) if v.starts_with("Bearer ") => {
            let token = v.trim_start_matches("Bearer ").trim();
            // 先尝试 JWT 验证，否则回退到固定 token
            validate_token(token).unwrap_or(false) || token == expected
        }
        _ => false,
    }
}
