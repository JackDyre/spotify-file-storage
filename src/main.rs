use sfs::auth::{authenticate, Credentials};
use sfs::request::UserID;

use anyhow::Result;

#[tokio::main]
async fn main() -> Result<()> {
    let creds = Credentials::from_env()?;

    let token = authenticate(creds).await?;

    let id = UserID::new(&token).await?;

    Ok(())
}
