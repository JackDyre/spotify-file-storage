use std::env;

use anyhow::{ensure, Result};
use base64::{engine::general_purpose::STANDARD as b64, Engine};
use dotenvy::dotenv;
use rand::{distributions::Alphanumeric, Rng};
use reqwest::header::{HeaderMap, HeaderValue, AUTHORIZATION, CONTENT_TYPE};
use serde::{Deserialize, Serialize};
use url::Url;

const PORT: i32 = 8888;
const AUTHORIZATION_BASE_URL: &str = "https://accounts.spotify.com/authorize";
const ACCESS_TOKEN_BASE_URL: &str = "https://accounts.spotify.com/api/token";

pub async fn authenticate(creds: Credentials<AuthCodeNotPresent>) -> Result<AccessToken> {
    creds.get_auth_code()?.get_access_token().await
}

pub struct AuthCodeNotPresent;
pub struct AuthCodePresent(String);

pub trait AuthCodeStates: private::Sealed {}
impl AuthCodeStates for AuthCodeNotPresent {}
impl AuthCodeStates for AuthCodePresent {}

pub struct Credentials<AuthCodeState>
where
    AuthCodeState: AuthCodeStates,
{
    pub client_id: String,
    pub client_secret: String,
    authorization_code: AuthCodeState,
    state: String,
}

impl Credentials<AuthCodeNotPresent> {
    pub fn new(client_id: &str, client_secret: &str) -> Credentials<AuthCodeNotPresent> {
        Credentials {
            client_id: String::from(client_id),
            client_secret: String::from(client_secret),
            authorization_code: AuthCodeNotPresent,
            state: rand::thread_rng()
                .sample_iter(&Alphanumeric)
                .take(64)
                .map(char::from)
                .collect(),
        }
    }

    pub fn from_env() -> Result<Credentials<AuthCodeNotPresent>> {
        dotenv().ok();

        let client_id = env::var("SFS_CLIENT_ID")?;
        let client_secret = env::var("SFS_CLIENT_SECRET")?;

        Ok(Credentials::new(&client_id, &client_secret))
    }

    pub fn get_auth_code(self) -> Result<Credentials<AuthCodePresent>> {
        let url_params = serde_urlencoded::to_string(AuthCodeRequest::new(&self))?;

        let auth_code_request_url =
            Url::parse(&format!("{}?{}", AUTHORIZATION_BASE_URL, url_params))?;

        let server = tiny_http::Server::http(format!("0.0.0.0:{PORT}"))
            .expect("Error starting http server.");
        webbrowser::open(auth_code_request_url.as_str())?;

        let request = server.recv()?;
        let callback_url = request.url();

        ensure!(
            callback_url.starts_with("/callback?"),
            "The captured callback url was malformed"
        );

        let callback = serde_urlencoded::from_str::<AuthCodeCallback>(&callback_url[10..])?;

        ensure!(
            callback.error.is_none(),
            "Authorization callback returned an error"
        );
        ensure!(
            callback.state == self.state,
            "State sent to Spotify does not match the one returned"
        );

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
            authorization_code: AuthCodePresent(auth_code.to_string()),
            state: self.state,
        }
    }
}

impl Credentials<AuthCodePresent> {
    pub async fn get_access_token(self) -> Result<AccessToken> {
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
            .post(ACCESS_TOKEN_BASE_URL)
            .headers(headers)
            .form(&[
                ("code", self.authorization_code.0),
                ("redirect_uri", format!("http://localhost:{PORT}/callback")),
                ("grant_type", "authorization_code".to_string()),
            ])
            .send()
            .await?;

        let token: AccessToken = serde_json::from_str(&response.text().await?)?;

        Ok(token)
    }
}

#[allow(unused)]
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
    fn new(creds: &Credentials<AuthCodeNotPresent>) -> AuthCodeRequest {
        AuthCodeRequest {
            client_id: creds.client_id.clone(),
            response_type: "code".to_string(),
            redirect_uri: format!("http://localhost:{PORT}/callback"),
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

mod private {
    pub trait Sealed {}
    impl Sealed for super::AuthCodeNotPresent {}
    impl Sealed for super::AuthCodePresent {}
}
