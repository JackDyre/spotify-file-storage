use sfs::spotify::auth::{authenticate, Credentials};

#[tokio::main]
async fn main() -> error_stack::Result<(), sfs::spotify::auth::SpotifyAuthError> {
    let token = authenticate(Credentials::from_env()?).await?;

    dbg!(token);

    Ok(())
}
