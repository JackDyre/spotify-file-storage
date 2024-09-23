use anyhow::Result;
use auth::AccessToken;
use id::UserID;

pub mod auth;
pub mod id;

#[derive(Debug)]
pub struct Spotify {
    access_token: AccessToken,
    user_id: UserID,
}

impl Spotify {
    pub async fn new(access_token: AccessToken) -> Result<Spotify> {
        Ok(Spotify {
            user_id: UserID::get(&access_token).await?,
            access_token,
        })
    }
}
