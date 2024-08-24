use serde::Deserialize;
use tiny_http::{Response, Server};
use url::Url;

fn main() {
    let server = Server::http("0.0.0.0:8000").unwrap();
    let request = server.recv().unwrap();
    let url = request.url().to_string();

    request
        .respond(Response::from_string("hello world"))
        .unwrap();

    let url = &Url::parse("http://localhost:8000")
        .unwrap()
        .join(&url)
        .unwrap();

    let query: AuthCallbackQuery = serde_urlencoded::from_str(url.query().unwrap()).unwrap();

    dbg!(query.code);
    dbg!(query.state);
}

#[derive(Debug, Deserialize)]
struct AuthCallbackQuery {
    code: String,
    state: String,
}
