use chrono::{Duration, Utc};
use jsonwebtoken::{decode, encode, Algorithm, DecodingKey, EncodingKey, Header, Validation};
use serde::{Deserialize, Serialize};
use std::env;

#[derive(Debug, Serialize, Deserialize)]
struct Claims {
    sub: String,
    exp: i64,
}

fn secret() -> String {
    env::var("JWT_SECRET").unwrap_or_else(|_| "dummy-secret".to_string())
}

pub fn issue_token(username: &str) -> String {
    let exp = Utc::now()
        .checked_add_signed(Duration::hours(1))
        .map(|t| t.timestamp())
        .unwrap_or_else(|| Utc::now().timestamp());
    let claims = Claims {
        sub: username.to_string(),
        exp,
    };
    encode(
        &Header::new(Algorithm::HS256),
        &claims,
        &EncodingKey::from_secret(secret().as_bytes()),
    )
    .unwrap_or_else(|_| "dummy-token".to_string())
}

pub fn validate_token(token: &str) -> jsonwebtoken::errors::Result<bool> {
    let validation = Validation::new(Algorithm::HS256);
    let token_data = decode::<Claims>(
        token,
        &DecodingKey::from_secret(secret().as_bytes()),
        &validation,
    )?;
    Ok(token_data.claims.exp >= Utc::now().timestamp())
}
