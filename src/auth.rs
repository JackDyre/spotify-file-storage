use crate::error::SfsError;
use base64::{engine::general_purpose::STANDARD as b64, Engine};
use reqwest::header::{HeaderMap, HeaderValue, AUTHORIZATION, CONTENT_TYPE};
use serde::{Deserialize, Serialize};
use std::fmt::Debug;
use std::{error::Error, marker::PhantomData};
use url::Url;

#[doc(hidden)]
pub struct NoAuthCode;
#[derive(Debug)]
pub struct AuthCodePresent;

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
            state: String::from("test"),
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

#[derive(Deserialize)]
pub struct AccessToken {
    pub access_token: String,
    _token_type: String,
    _scope: String,
    _expires_in: i32,
    _refresh_token: String,
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
