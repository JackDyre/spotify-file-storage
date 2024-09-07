use base64::{engine::general_purpose::STANDARD as b64, Engine};
use reqwest::header::{HeaderMap, HeaderValue, AUTHORIZATION, CONTENT_TYPE};
use serde::{Deserialize, Serialize};
use std::error::Error;
use std::fmt::Debug;
use tiny_http::Server;
use url::Url;

#[derive(Deserialize, Debug)]
pub struct AccessToken {
    access_token: String,
    expires_in: i32,
    refresh_token: String,
    scope: String,
    token_type: String,
}

pub async fn auth(creds: Creds) -> Result<AccessToken, Box<dyn Error>> {
    let auth_code = creds.to_auth_code_request();

    let url = url::Url::try_from(auth_code)?.to_string();

    let creds = AuthCodeCallback::capture(&url, creds);

    let token = get_token(&creds).await?;

    dbg!(&token);

    Ok(token)
}

async fn get_token(creds: &Creds) -> Result<AccessToken, String> {
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
    headers.insert(
        AUTHORIZATION,
        HeaderValue::from_str(&auth_header_val).unwrap(),
    );

    let response = reqwest::Client::new()
        .post("https://accounts.spotify.com/api/token")
        .headers(headers)
        .form(&[
            ("code", creds.code.unwrap()),
            ("redirect_uri", "http://localhost:8888/callback".to_string()),
            ("grant_type", "authorization_code".to_string()),
        ])
        .send()
        .await
        .unwrap();

    let token = response.text().await.unwrap();

    Ok(serde_json::from_str::<AccessToken>(&token).unwrap())
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

    fn to_auth_code_request(&self) -> AuthCode {
        AuthCode {
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
struct AuthCode {
    client_id: String,
    response_type: String,
    redirect_uri: String,
    scope: String,
}

impl TryFrom<AuthCode> for Url {
    type Error = String;

    fn try_from(auth_code: AuthCode) -> Result<Url, String> {
        let url_encoded_query = match serde_urlencoded::to_string(auth_code) {
            Ok(query) => query,
            Err(e) => return Err(e.to_string()),
        };

        let url_string = format!(
            "https://accounts.spotify.com/authorize?{}",
            url_encoded_query,
        );

        let parsed_url = match Url::parse(&url_string) {
            Ok(url) => url,
            Err(e) => return Err(e.to_string()),
        };

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
    fn parse_callback_url(url: &str, creds: Creds) -> Result<Creds, String> {
        if !url.starts_with("/callback?") {
            return Err(String::from("Error while trying to parse callback url."));
        }

        let callback: AuthCodeCallback = serde_urlencoded::from_str(&url[10..]).unwrap();

        match callback.error {
            Some(_) => return Err(String::from("Error during authentication")),
            None => (),
        };

        Ok(Creds {
            id: creds.id,
            secret: creds.secret,
            code: callback.code,
        })
    }

    fn capture(url: &str, creds: Creds) -> Creds {
        let server = Server::http("0.0.0.0:8888").unwrap();
        webbrowser::open(&url).unwrap();
        let request = server.recv().unwrap();
        let callback = AuthCodeCallback::parse_callback_url(&request.url(), creds).unwrap();
        callback
    }
}
