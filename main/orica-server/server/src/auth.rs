use axum::http::HeaderMap;

// 简单 token 校验占位，需替换为真实 JWT 验证
pub fn check_auth(headers: &HeaderMap) -> bool {
    if let Some(value) = headers.get("authorization") {
        if let Ok(token) = value.to_str() {
            return token.starts_with("Bearer ");
        }
    }
    false
}
