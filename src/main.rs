use sfs::Credentials;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let creds = Creds::new("", "");
    creds.get_auth_code()?;

    Ok(())
}
