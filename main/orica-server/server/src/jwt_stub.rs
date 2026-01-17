pub fn issue_token(username: &str) -> String {
    // 简易：返回 Bearer + 用户名，实际应签发 JWT
    format!("dummy-{}", username)
}
