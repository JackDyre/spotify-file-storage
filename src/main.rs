use sfs::{auth, Creds};

#[tokio::main]
    let creds = Creds::new("", "");
async fn main() -> Result<(), Box<dyn std::error::Error>> {

    auth(creds).await?;

    Ok(())
}
