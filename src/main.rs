use sfs::*;
use url::Url;

#[tokio::main]
async fn main() {
    let creds = Creds::new(
        "592557b25f744f2abdd7234c2d668346",
        "2ce9de831a524fd7b1231929d9f3abcd",
    );

    let auth_code: AuthCode = creds.into();

    let url = Url::try_from(auth_code).unwrap().to_string();

    dbg!(url);

}

