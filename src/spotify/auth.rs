use error_stack::{bail, report, Result, ResultExt};
use rand::{distributions::Alphanumeric, Rng};
use reqwest::header::{HeaderValue, CONTENT_TYPE};
use serde::{Deserialize, Serialize};
use std::env;
use url::Url;

const PORT: i32 = 8888;
const AUTHORIZATION_BASE_URL: &str = "https://accounts.spotify.com/authorize";
const ACCESS_TOKEN_BASE_URL: &str = "https://accounts.spotify.com/api/token";

pub async fn authenticate(creds: Credentials<AuthCodeNotPresent>) -> anyhow::Result<AccessToken> {
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

    pub fn from_env() -> anyhow::Result<Credentials<AuthCodeNotPresent>> {
        dotenvy::dotenv()?;
        let client_id = env::var("SFS_CLIENT_ID")?;
        let client_secret = env::var("SFS_CLIENT_SECRET")?;
        Ok(Credentials::new(&client_id, &client_secret))
    }

    pub fn get_auth_code(self) -> anyhow::Result<Credentials<AuthCodePresent>> {
        let auth_code = CallbackCaptureServer::new(&self)?.capture()?;
        Ok(self.add_auth_code(auth_code))
    }

    fn add_auth_code(self, auth_code: String) -> Credentials<AuthCodePresent> {
        Credentials {
            client_id: self.client_id,
            client_secret: self.client_secret,
            authorization_code: AuthCodePresent(auth_code),
            state: self.state,
        }
    }
}

impl Credentials<AuthCodePresent> {
    pub async fn get_access_token(self) -> anyhow::Result<AccessToken> {
        let response = reqwest::Client::new()
            .post(ACCESS_TOKEN_BASE_URL)
            .basic_auth(self.client_id, Some(self.client_secret))
            .header(
                CONTENT_TYPE,
                HeaderValue::from_static("application/x-www-form-urlencoded"),
            )
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

impl AuthCodeCallback {
    fn parse_for_code(self, state: String) -> Result<String, SpotifyAuthError> {
        if self.error.is_some() {
            bail!(report!(SpotifyAuthError::Error(
                "Authorization callback returned an error"
            ))
            .attach_printable(self.error.unwrap_or_default()))
        }
        if state != self.state {
            bail!(report!(SpotifyAuthError::Error(
                "State sent to Spotify does not match the one returned"
            ))
            .attach_printable(state)
            .attach_printable(self.state))
        }
        let code = match self.code {
            Some(c) => c,
            None => bail!(report!(SpotifyAuthError::Error(
                "Auth code not present in callback"
            ))),
        };
        Ok(code)
    }
}

struct CallbackCaptureServer {
    server: tiny_http::Server,
    prompt_url: String,
    state: String,
}

impl CallbackCaptureServer {
    fn new(creds: &Credentials<AuthCodeNotPresent>) -> anyhow::Result<CallbackCaptureServer> {
        let server = match tiny_http::Server::http(format!("0.0.0.0:{PORT}")) {
            Ok(s) => s,
            Err(e) => anyhow::bail!(e),
        };
        let prompt_url_params = serde_urlencoded::to_string(AuthCodeRequest::new(&creds))?;
        Ok(CallbackCaptureServer {
            server,
            prompt_url: Url::parse(&format!("{}?{}", AUTHORIZATION_BASE_URL, prompt_url_params))?
                .to_string(),
            state: creds.state.clone(),
        })
    }

    fn capture(self) -> Result<String, SpotifyAuthError> {
        webbrowser::open(&self.prompt_url).change_context(SpotifyAuthError::Error(
            "Error opening authorization prompt url",
        ))?;
        let request = self.server.recv().change_context(SpotifyAuthError::Error(
            "Error receiving auth code callback request",
        ))?;

        let url = &request.url();

        let callback_url = if url.starts_with("/callback?") {
            &url.clone()[10..]
        } else {
            bail!(report!(SpotifyAuthError::Error(
                "Auth code callback url was malformed"
            ))
            .attach_printable(url.clone()))
        };

        let callback = serde_urlencoded::from_str::<AuthCodeCallback>(callback_url)
            .change_context(SpotifyAuthError::Error(
                "Error while parsing auth code callback",
            ))
            .attach_printable(callback_url)?;

        let code = callback
            .parse_for_code(self.state)
            .change_context(SpotifyAuthError::Error(
                "Error while parsing auth code callback",
            ))
            .attach_printable(callback_url)?;

        request
            .respond(
                tiny_http::Response::from_string(
                    "<html><body><script>window.close();</script></body></html>",
                )
                .with_header(tiny_http::Header {
                    field: "Content-Type".parse().unwrap(),
                    value: "text/html".parse().unwrap(),
                }),
            )
            .change_context(SpotifyAuthError::Error(
                "Error responding to auth code callback request",
            ))?;

        Ok(code)
    }
}

#[derive(thiserror::Error, Debug)]
pub enum SpotifyAuthError {
    #[error("{0}")]
    Error(&'static str),
}

mod private {
    pub trait Sealed {}
    impl Sealed for super::AuthCodeNotPresent {}
    impl Sealed for super::AuthCodePresent {}
}
