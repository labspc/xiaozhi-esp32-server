/// 占位：替换为真实 JWT 验证与签发
pub fn issue_token(username: &str) -> String {
    // 简易：返回 Bearer + 用户名，实际应签发 JWT
    format!("dummy-{}", username)
}
