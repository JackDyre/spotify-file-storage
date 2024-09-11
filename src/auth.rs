use base64::{engine::general_purpose::STANDARD as b64, Engine};
use rand::{distributions::Alphanumeric, Rng};
use reqwest::header::{HeaderMap, HeaderValue, AUTHORIZATION, CONTENT_TYPE};
use serde::{Deserialize, Serialize};
use std::{error::Error, marker::PhantomData};
use url::Url;

use crate::error::SfsError;

pub async fn authenticate(creds: &Credentials<NoAuthCode>) -> Result<AccessToken, Box<dyn Error>> {
    let creds = creds.clone();
    let creds = creds.get_auth_code()?;
    let token = creds.get_access_token().await?;
    Ok(token)
}

#[doc(hidden)]
#[derive(Clone)]
pub struct NoAuthCode;
#[doc(hidden)]
#[derive(Clone)]
pub struct AuthCodePresent;

#[derive(Clone)]
pub struct Credentials<State> {
    pub client_id: String,
    pub client_secret: String,
    authorization_code: Option<String>,
    state: String,
    auth_code_state: PhantomData<State>,
}

impl Credentials<NoAuthCode> {
    pub fn new(client_id: &str, client_secret: &str) -> Credentials<NoAuthCode> {
        Credentials {
            client_id: String::from(client_id),
            client_secret: String::from(client_secret),
            authorization_code: None,
            state: rand::thread_rng()
                .sample_iter(&Alphanumeric)
                .take(64)
                .map(char::from)
                .collect(),
            auth_code_state: PhantomData,
        }
    }

    pub fn get_auth_code(self) -> Result<Credentials<AuthCodePresent>, Box<dyn Error>> {
        let base_url = "https://accounts.spotify.com/authorize?";

        let auth_code_request = AuthCodeRequest::new(&self);
        let url_params = serde_urlencoded::to_string(&auth_code_request)?;

        let auth_code_request_url = Url::parse(&format!("{}{}", base_url, url_params))?;

        let server = tiny_http::Server::http("0.0.0.0:8888").unwrap();
        webbrowser::open(auth_code_request_url.as_str())?;

        let request = server.recv()?;
        let callback_url = request.url();

        if !callback_url.starts_with("/callback?") {
            return Err(SfsError::new_box("Error parsing callback url"));
        }

        let callback = serde_urlencoded::from_str::<AuthCodeCallback>(&callback_url[10..])?;

        if callback.error.is_some() {
            return Err(SfsError::new_box("Error during authentication."));
        }
        if &callback.state != &self.state {
            return Err(SfsError::new_box("Mismatched states"));
        }

        request.respond(
            tiny_http::Response::from_string(
                "<html><body><script>window.close();</script></body></html>",
            )
            .with_header(tiny_http::Header {
                field: "Content-Type".parse().unwrap(),
                value: "text/html".parse().unwrap(),
            }),
        )?;

        Ok(self.add_auth_code(&callback.code.unwrap()))
    }

    fn add_auth_code(self, auth_code: &str) -> Credentials<AuthCodePresent> {
        Credentials {
            client_id: self.client_id,
            client_secret: self.client_secret,
            authorization_code: Some(auth_code.to_string()),
            state: self.state,
            auth_code_state: PhantomData,
        }
    }
}

impl Credentials<AuthCodePresent> {
    pub async fn get_access_token(&self) -> Result<AccessToken, Box<dyn Error>> {
        let mut headers = HeaderMap::new();
        headers.insert(
            CONTENT_TYPE,
            HeaderValue::from_static("application/x-www-form-urlencoded"),
        );
        headers.insert(
            AUTHORIZATION,
            HeaderValue::from_str(&format!(
                "Basic {}",
                b64.encode(format!("{}:{}", self.client_id, self.client_secret))
            ))?,
        );

        let response = reqwest::Client::new()
            .post("https://accounts.spotify.com/api/token")
            .headers(headers)
            .form(&[
                ("code", self.authorization_code.clone().unwrap()),
                ("redirect_uri", "http://localhost:8888/callback".to_string()),
                ("grant_type", "authorization_code".to_string()),
            ])
            .send()
            .await?;

        let token: AccessToken = serde_json::from_str(&response.text().await?)?;

        Ok(token)
    }
}

#[derive(Deserialize, Debug)]
pub struct AccessToken {
    pub access_token: String,
    token_type: String,
    scope: String,
    expires_in: i32,
    refresh_token: String,
}

#[derive(Serialize)]
struct AuthCodeRequest {
    client_id: String,
    response_type: String,
    redirect_uri: String,
    state: String,
    scope: String,
}

impl AuthCodeRequest {
    fn new(creds: &Credentials<NoAuthCode>) -> AuthCodeRequest {
        AuthCodeRequest {
            client_id: creds.client_id.clone(),
            response_type: "code".to_string(),
            redirect_uri: "http://localhost:8888/callback".to_string(),
            state: creds.state.clone(),
            scope: format!(
                "{} {} {}",
                "playlist-read-private", "playlist-modify-public", "playlist-modify-private"
            ),
        }
    }
}

#[derive(Deserialize)]
struct AuthCodeCallback {
    code: Option<String>,
    error: Option<String>,
    state: String,
}
