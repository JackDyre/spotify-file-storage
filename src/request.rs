use anyhow::Result;
use reqwest::header::{HeaderValue, AUTHORIZATION};
use serde::Deserialize;

use crate::auth::AccessToken;

#[derive(Debug, Deserialize)]
pub struct UserID {
    pub id: String,
}

impl UserID {
    pub async fn new(token: &AccessToken) -> Result<UserID> {
        let response: UserID = serde_json::from_str(
            &reqwest::Client::new()
                .get("https://api.spotify.com/v1/me")
                .header(
                    AUTHORIZATION,
                    HeaderValue::from_str(&format!("Bearer {}", token.access_token))?,
                )
                .send()
                .await?
                .text()
                .await?,
        )?;

        Ok(response)
    }
}
