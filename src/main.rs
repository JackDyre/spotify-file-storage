use url::Url;

#[tokio::main]
async fn main() {

}

struct Creds {
    id: String,
    secret: String,
}

impl Creds {
    fn new(id: &str, secret: &str) -> Creds {
        Creds {
            id: String::from(id),
            secret: String::from(secret),
        }
    }
}

async fn auth(creds: Creds) -> Result<(), String> {
    let url = Url::parse("https://accounts.spotify.com/authorize");
    todo!();
    Ok(())
}

struct AuthCode {
    client_id: String,
    response_type: String,
    redirect_uri: String,
    scope: String,
}

impl From<Creds> for AuthCode {
    fn from<Creds>:wqwa
}
