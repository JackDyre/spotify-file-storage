use sfs::{auth, Creds};

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let creds = Creds::new("", "");

    let token = auth(creds).await?;

    dbg!(token);

    Ok(())
}
