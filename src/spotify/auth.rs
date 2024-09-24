use error_stack::{bail, report, ResultExt};
use rand::{distributions::Alphanumeric, Rng};
use reqwest::header::{HeaderValue, CONTENT_TYPE};
use serde::{Deserialize, Serialize};
use std::env;
use url::Url;

type Result<T> = error_stack::Result<T, SpotifyAuthError>;

const PORT: i32 = 8888;
const AUTHORIZATION_BASE_URL: &str = "https://accounts.spotify.com/authorize";
const ACCESS_TOKEN_BASE_URL: &str = "https://accounts.spotify.com/api/token";

pub async fn authenticate(creds: Credentials<AuthCodeNotPresent>) -> Result<AccessToken> {
    Ok(creds
        .get_auth_code()
        .change_context(new_error("Error while getting auth code"))?
        .get_access_token()
        .await
        .change_context(new_error(
            "Error while exchanging auth code for access token",
        ))?)
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
        dotenvy::dotenv().change_context(new_error("Error while attempting to read .env file"))?;
        let client_id = env::var("SFS_CLIENT_ID").change_context(new_error(
            "Error while attempting to get client ID forom environment variables",
        ))?;
        let client_secret = env::var("SFS_CLIENT_SECRET").change_context(new_error(
            "Error while attempting to get client secret forom environment variables",
        ))?;
        Ok(Credentials::new(&client_id, &client_secret))
    }

    pub fn get_auth_code(self) -> Result<Credentials<AuthCodePresent>> {
        let auth_code = CallbackCaptureServer::new(&self)
            .change_context(new_error(
                "Unable create http server to capture auth code callback",
            ))?
            .capture()
            .change_context(new_error("Error capturing auth code callback"))?;
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
    pub async fn get_access_token(self) -> Result<AccessToken> {
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
            .await
            .change_context(new_error("Error sending request for access token"))?;

        let token: AccessToken = serde_json::from_str(&response.text().await.change_context(
            new_error("Unable to get text from access token request response"),
        )?)
        .change_context(new_error("Unable to parse acess token request response"))?;

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
    fn parse_for_code(self, state: String) -> Result<String> {
        if self.error.is_some() {
            bail!(
                report!(new_error("Authorization callback returned an error"))
                    .attach_printable(self.error.unwrap_or_default())
            )
        }
        if state != self.state {
            bail!(report!(new_error(
                "State sent to Spotify does not match the one returned"
            ))
            .attach_printable(state)
            .attach_printable(self.state))
        }
        let code = match self.code {
            Some(c) => c,
            None => bail!(report!(new_error("Auth code not present in callback"))),
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
    fn new(creds: &Credentials<AuthCodeNotPresent>) -> Result<CallbackCaptureServer> {
        let server = match tiny_http::Server::http(format!("0.0.0.0:{PORT}")) {
            Ok(s) => s,
            Err(_) => bail!(new_error("Unable to start http server")),
        };
        let prompt_url_params = serde_urlencoded::to_string(AuthCodeRequest::new(&creds))
            .change_context(new_error("Error url-encoding authorization query"))?;
        Ok(CallbackCaptureServer {
            server,
            prompt_url: Url::parse(&format!("{}?{}", AUTHORIZATION_BASE_URL, prompt_url_params))
                .change_context(new_error("Unable to parse authorization prompt url"))?
                .to_string(),
            state: creds.state.clone(),
        })
    }

    fn capture(self) -> Result<String> {
        webbrowser::open(&self.prompt_url)
            .change_context(new_error("Error opening authorization prompt url"))?;
        let request = self
            .server
            .recv()
            .change_context(new_error("Error receiving auth code callback request"))?;

        let url = &request.url();

        let callback_url = if url.starts_with("/callback?") {
            &url[10..]
        } else {
            bail!(new_error("Auth code callback url was malformed"))
        };

        let callback = serde_urlencoded::from_str::<AuthCodeCallback>(callback_url)
            .change_context(new_error("Error while parsing auth code callback"))?;

        let code = callback
            .parse_for_code(self.state)
            .change_context(new_error("Error while parsing auth code callback"))?;

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
            .change_context(new_error("Error responding to auth code callback request"))?;

        Ok(code)
    }
}

#[derive(thiserror::Error, Debug)]
pub enum SpotifyAuthError {
    #[error("{0}")]
    Error(&'static str),
}

fn new_error(msg: &'static str) -> SpotifyAuthError {
    SpotifyAuthError::Error(msg)
}

mod private {
    pub trait Sealed {}
    impl Sealed for super::AuthCodeNotPresent {}
    impl Sealed for super::AuthCodePresent {}
}
