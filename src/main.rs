use reqwest::blocking::Client;
use reqwest::header::{HeaderMap, HeaderValue, AUTHORIZATION, CONTENT_TYPE};
use serde::{Deserialize, Serialize};
use tiny_http::{Response, Server};
use url::Url;

const PORT: &str = "8888";
const REDIRECT_URI: &str = "http://localhost:8888/callback";

fn main() {
    let client_id = "MY_CLIENT_ID";
    let client_secret = "MY_CLIENT_SECRET";

    let auth_code_request = AuthCodeRequest::new(
        client_id,
        "test_state",
        "playlist-read-private playlist-modify-public playlist-modify-private",
    );
    let url = auth_code_request.to_url();

    let server = Server::http(format!("0.0.0.0:{}", PORT)).unwrap();
    webbrowser::open(url.as_ref()).unwrap();
    let request = server.recv().unwrap();
    let url = request.url().to_string();

    if !url.starts_with("/callback?") {
        panic!();
    }

    let raw_query = &url[10..];

    request
        .respond(Response::from_string("hello world"))
        .unwrap();

    let query: AuthCallbackQuery = serde_urlencoded::from_str(raw_query).unwrap();
    dbg!(&query.code);
    dbg!(query.state);

    let access_token_request = AccessTokenRequest::new(&query.code, client_id, client_secret);

    access_token_request.send();
}

#[derive(Debug, Deserialize)]
struct AuthCallbackQuery {
    code: String,
    state: String,
}

#[derive(Serialize, Debug)]
struct AuthCodeRequest {
    client_id: String,
    response_type: String,
    redirect_uri: String,
    state: Option<String>,
    scope: Option<String>,
    show_dialog: Option<String>,
}

impl AuthCodeRequest {
    fn new(client_id: &str, state: &str, scope: &str) -> AuthCodeRequest {
        AuthCodeRequest {
            client_id: String::from(client_id),
            response_type: String::from("code"),
            redirect_uri: format!("http://localhost:{}/callback", PORT),
            state: Some(String::from(state)),
            scope: Some(String::from(scope)),
            show_dialog: None,
        }
    }

    fn to_url(&self) -> Url {
        let base_url = "https://accounts.spotify.com/authorize?";
        let ser_query = serde_urlencoded::to_string(self).unwrap();
        let url = &format!("{}{}", base_url, ser_query);
        Url::parse(url).unwrap()
    }
}

#[derive(Debug)]
struct AccessTokenRequest {
    query: AccessTokenRequestQuery,
    headers: AccessTokenRequestHeaders,
}

impl AccessTokenRequest {
    fn new(code: &str, client_id: &str, client_secret: &str) -> AccessTokenRequest {
        AccessTokenRequest {
            query: AccessTokenRequestQuery::new(code),
            headers: AccessTokenRequestHeaders::new(client_id, client_secret),
        }
    }

    fn send(&self) {
        let client = Client::new();

        let url = self.query.to_url();

        let headers = self.headers.to_headermap();

        let response = client.post(url).headers(headers).send().unwrap();

        dbg!(response);
    }
}

#[derive(Debug, Serialize)]
struct AccessTokenRequestQuery {
    grant_type: String,
    code: String,
    redirect_uri: String,
}

impl AccessTokenRequestQuery {
    fn new(code: &str) -> AccessTokenRequestQuery {
        AccessTokenRequestQuery {
            grant_type: String::from("authorization_code"),
            code: String::from(code),
            redirect_uri: String::from(REDIRECT_URI),
        }
    }

    fn to_url(&self) -> Url {
        let base_url = "https://accounts.spotify.com/api/token";
        let ser_query = serde_urlencoded::to_string(self).unwrap();
        let url = &format!("{}{}", base_url, ser_query);
        Url::parse(url).unwrap()
    }
}

#[derive(Debug)]
struct AccessTokenRequestHeaders {
    authorization: String,
    content_type: String,
}

impl AccessTokenRequestHeaders {
    fn new(client_id: &str, client_secret: &str) -> AccessTokenRequestHeaders {
        AccessTokenRequestHeaders {
            authorization: format!("Basic {}:{}", client_id, client_secret),
            content_type: String::from("application/x-www-form-urlencoded"),
        }
    }

    fn to_headermap(&self) -> HeaderMap {
        let mut headers = HeaderMap::new();

        headers.insert(
            AUTHORIZATION,
            HeaderValue::from_str(&self.authorization).unwrap(),
        );
        headers.insert(
            CONTENT_TYPE,
            HeaderValue::from_str(&self.content_type).unwrap(),
        );

        headers
    }
}
