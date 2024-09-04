use std::fmt::Debug;

use serde::{Deserialize, Serialize};
use tiny_http::Server;
use url::Url;

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
}

pub async fn auth(creds: Creds) -> Result<(), String> {
    let auth_code: AuthCode = creds.clone().into();
    let url = url::Url::try_from(auth_code)?.to_string();
    let callback = capture_callback(&url);
    let creds = parse_callback(creds, callback)?;
    dbg!(creds);
    Ok(())
}

fn capture_callback(url: &str) -> AuthCodeCallback {
    let server = Server::http("0.0.0.0:8888").unwrap();
    webbrowser::open(&url).unwrap();
    let request = server.recv().unwrap();
    let callback = AuthCodeCallback::parse_callback_url(&request.url()).unwrap();
    callback
}

fn parse_callback(creds: Creds, callback: AuthCodeCallback) -> Result<Creds, String> {
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

#[derive(Debug, Serialize)]
pub struct AuthCode {
    client_id: String,
    response_type: String,
    redirect_uri: String,
    scope: String,
}

impl From<Creds> for AuthCode {
    fn from(creds: Creds) -> AuthCode {
        AuthCode {
            client_id: creds.id,
            response_type: String::from("code"),
            redirect_uri: String::from("http://localhost:8888/callback"),
            scope: format!(
                "{} {} {}",
                "playlist-read-private", "playlist-modify-public", "playlist-modify-private"
            ),
        }
    }
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
    fn parse_callback_url(url: &str) -> Result<AuthCodeCallback, String> {
        if !url.starts_with("/callback?") {
            return Err(String::from("Error while trying to parse callback url."));
        }

        Ok(serde_urlencoded::from_str(&url[10..]).unwrap())
    }
}
