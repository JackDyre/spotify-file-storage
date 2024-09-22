use sfs::auth::{authenticate, Credentials};
use sfs::request::*;

use anyhow::Result;

#[tokio::main]
async fn main() -> Result<()> {
    let creds = Credentials::from_env()?;

    let token = authenticate(creds).await?;

    let _id = UserID::new(&token).await?;

    Ok(())
}
