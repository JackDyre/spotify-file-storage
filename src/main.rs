use sfs::auth::{authenticate, Credentials};

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let creds = Credentials::new("", "");

    let token = authenticate(&creds).await?;

    dbg!(token);

    Ok(())
}
