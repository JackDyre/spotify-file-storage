use sfs::spotify::{
    auth::{authenticate, Credentials},
    Spotify,
};

use anyhow::Result;

#[tokio::main]
async fn main() -> Result<()> {
    let token = authenticate(Credentials::from_env()?).await?;

    let spotify = Spotify::new(token).await?;

    dbg!(spotify);

    Ok(())
}
