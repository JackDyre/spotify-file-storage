//! # auth
//!
//! Handles authentication with the Spotify Web API
//!
//! ### Basic flow:
//! - Url-encode api credentials
//! - Open the url for the user to authenticate
//! - Listen for the user to be redirected to localhost and capture the authorization code
//! - Send a POST with the authorization code to receive the access token
//!
//! **Warning:** This module's public api is subject to change

use crate::error::SfsError;
use base64::{engine::general_purpose::STANDARD as b64, Engine};
use reqwest::header::{HeaderMap, HeaderValue, AUTHORIZATION, CONTENT_TYPE};
use serde::{Deserialize, Serialize};
use std::error::Error;
use std::fmt::Debug;
use tiny_http::{Response, Server};
use url::Url;

pub async fn auth(creds: Creds) -> Result<AccessToken, Box<dyn Error>> {
    let auth_code = creds.to_auth_code_request();

    let url = url::Url::try_from(auth_code)?.to_string();

    let creds = AuthCodeCallback::capture(&url, creds)?;

    let token = AccessToken::get_token(&creds).await?;

    Ok(token)
}

#[derive(Deserialize, Debug)]
pub struct AccessToken {
    pub access_token: String,
    pub expires_in: i32,
    pub refresh_token: String,
    pub scope: String,
    pub token_type: String,
}

impl AccessToken {
    async fn get_token(creds: &Creds) -> Result<AccessToken, Box<dyn Error>> {
        let creds = creds.clone();
        let auth_header_val = format!(
            "Basic {}",
            b64.encode(format!("{}:{}", creds.id, creds.secret))
        );
        let mut headers = HeaderMap::new();
        headers.insert(
            CONTENT_TYPE,
            HeaderValue::from_static("application/x-www-form-urlencoded"),
        );
        headers.insert(AUTHORIZATION, HeaderValue::from_str(&auth_header_val)?);

        let response = reqwest::Client::new()
            .post("https://accounts.spotify.com/api/token")
            .headers(headers)
            .form(&[
                ("code", creds.code.unwrap_or_default()),
                ("redirect_uri", "http://localhost:8888/callback".to_string()),
                ("grant_type", "authorization_code".to_string()),
            ])
            .send()
            .await?;

        let token = response.text().await?;

        Ok(serde_json::from_str::<AccessToken>(&token)?)
    }
}

#[derive(Debug, Clone)]
pub struct Creds {
    id: String,
    secret: String,
    code: Option<String>,
}

impl Creds {
    pub fn new(id: &str, secret: &str) -> Creds {
        Creds {
            id: String::from(id),
            secret: String::from(secret),
            code: None,
        }
    }

    fn to_auth_code_request(&self) -> AuthCodeRequest {
        AuthCodeRequest {
            client_id: self.id.clone(),
            response_type: String::from("code"),
            redirect_uri: String::from("http://localhost:8888/callback"),
            scope: format!(
                "{} {} {}",
                "playlist-read-private", "playlist-modify-public", "playlist-modify-private"
            ),
        }
    }
}

#[derive(Debug, Serialize)]
struct AuthCodeRequest {
    client_id: String,
    response_type: String,
    redirect_uri: String,
    scope: String,
}

impl TryFrom<AuthCodeRequest> for Url {
    type Error = Box<dyn Error>;

    fn try_from(auth_code: AuthCodeRequest) -> Result<Url, Box<dyn Error>> {
        let url_encoded_query = serde_urlencoded::to_string(auth_code)?;

        let url_string = format!("https://accounts.spotify.com/authorize?{url_encoded_query}",);

        let parsed_url = Url::parse(&url_string)?;

        Ok(parsed_url)
    }
}

#[derive(Deserialize, Debug)]
struct AuthCodeCallback {
    code: Option<String>,
    error: Option<String>,
    _state: Option<String>,
}

impl AuthCodeCallback {
    fn parse_callback_url(url: &str, creds: Creds) -> Result<Creds, Box<dyn Error>> {
        if !url.starts_with("/callback?") {
            return Err(SfsError::new_box("Error parsing callback url"));
        }

        let callback: AuthCodeCallback = serde_urlencoded::from_str(&url[10..])?;

        if callback.error.is_some() {
            return Err(SfsError::new_box("Error during authentication."));
        }

        Ok(Creds {
            id: creds.id,
            secret: creds.secret,
            code: callback.code,
        })
    }

    fn capture(url: &str, creds: Creds) -> Result<Creds, Box<dyn Error>> {
        let server;
        if let Ok(callback_server) = Server::http("0.0.0.0:8888") {
            server = callback_server;
        } else {
            return Err(SfsError::new_box("Error starting http server"));
        }

        webbrowser::open(url)?;
        let request = server.recv()?;
        let callback = AuthCodeCallback::parse_callback_url(request.url(), creds)?;

        request.respond(
            Response::from_string("<html><body><script>window.close();</script></body></html>")
                .with_header(tiny_http::Header {
                    field: "Content-Type".parse().unwrap(),
                    value: "text/html".parse().unwrap(),
                }),
        )?;

        Ok(callback)
    }
}
