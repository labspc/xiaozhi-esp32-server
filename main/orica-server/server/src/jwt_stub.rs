// 占位：替换为真实 JWT 验证与签发
pub fn validate_bearer(token: &str) -> bool {
    token.starts_with("Bearer ")
}

pub fn issue_token(username: &str) -> String {
    format!("dummy-{}", username)
}
