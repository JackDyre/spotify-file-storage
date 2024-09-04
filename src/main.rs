use sfs::{auth, Creds};

#[tokio::main]
async fn main() {
    let creds = Creds::new(
        "",
        "",
    );

    auth(creds).await.unwrap();

    println!("hello world")
}
