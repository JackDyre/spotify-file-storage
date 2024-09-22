use sfs::spotify::auth::{authenticate, Credentials};
use sfs::spotify::id::*;

use anyhow::Result;

#[tokio::main]
async fn main() -> Result<()> {
    let creds = Credentials::from_env()?;

    let token = authenticate(creds).await?;

    let user_id = UserID::get(&token).await?;

    dbg!(user_id.id());
    dbg!(user_id.uri());
    dbg!(user_id.url());

    Ok(())
}
