use serde::Serialize;
use url::Url;

#[derive(Debug)]
pub struct Creds {
    id: String,
    secret: String,
}

impl Creds {
    pub fn new(id: &str, secret: &str) -> Creds {
        Creds {
            id: String::from(id),
            secret: String::from(secret),
        }
    }
}

// async fn auth(creds: Creds) -> Result<(), String> {
// todo!();
//}

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
            redirect_uri: String::from("http://localhost:8000/callback"),
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
