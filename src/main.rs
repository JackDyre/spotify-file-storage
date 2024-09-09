use sfs::Credentials;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let creds = Credentials::new("", "");
    let creds = creds.get_auth_code()?;

    let token = creds.get_access_token().await?;

    dbg!(token);

    Ok(())
}
