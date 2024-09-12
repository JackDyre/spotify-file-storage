use anyhow::Result;
use sfs::auth::{authenticate, Credentials};

#[tokio::main]
async fn main() -> Result<()> {
    let creds = Credentials::new("", "");

    let token = authenticate(&creds).await?;

    dbg!(token);

    Ok(())
}
