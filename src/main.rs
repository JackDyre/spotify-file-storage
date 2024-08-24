use serde::Deserialize;
use tiny_http::{Response, Server};
// use url::Url;

const PORT: &str = "7551";

fn main() {
    let auth_code_request = AuthCodeRequest::new("MY_CLIENT_ID", "test_state", "playlist-read-private playlist-modify-public playlist-modify-private");

    let server = Server::http(format!("0.0.0.0:{}", PORT)).unwrap();
    let request = server.recv().unwrap();
    let url = request.url().to_string();

    if !url.starts_with("/callback?") {
        panic!();
    }

    let raw_query = &url[10..];
    dbg!(&raw_query);

    request
        .respond(Response::from_string("hello world"))
        .unwrap();


    let query: AuthCallbackQuery = serde_urlencoded::from_str(raw_query).unwrap();

    dbg!(query.code);
    dbg!(query.state);
}

#[derive(Debug, Deserialize)]
struct AuthCallbackQuery {
    code: String,
    state: String,
}

struct AuthCodeRequest {
    base_url: String,
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
            base_url: String::from("https://accounts.spotify.com/authorize"),
            client_id: String::from(client_id),
            response_type: String::from("code"),
            redirect_uri: format!("http://localhost:{}/callback", PORT),
            state: Some(String::from(state)),
            scope: Some(String::from(scope)),
            show_dialog: None,
        }
    }
}
