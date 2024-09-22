use anyhow::{bail, ensure, Result};
use regex::Regex;
use reqwest::header::{HeaderValue, AUTHORIZATION};
use std::marker::PhantomData;

use crate::auth::AccessToken;

pub type UserID = GenericResourceIdentifier<User>;
pub type PlaylistID = GenericResourceIdentifier<Playlist>;
pub type TrackID = GenericResourceIdentifier<Track>;

const ID_REGEX: &'static str = r"^[0-9A-Za-z]{22,28}$";
const URI_REGEX: &'static str = r"^spotify:(track|playlist|user):([0-9A-Za-z]{22,28})$";
const URL_REGEX: &'static str = r"^https:\/\/open\.spotify\.com\/(track|playlist|user)\/([0-9A-Za-z]{22,28})(\?si=[0-9A-Za-z]+)?$";

pub trait ResourceTypes {
    const NAME: &'static str;
}
#[derive(Debug)]
pub struct Track;
impl ResourceTypes for Track {
    const NAME: &'static str = "track";
}
#[derive(Debug)]
pub struct Playlist;
impl ResourceTypes for Playlist {
    const NAME: &'static str = "playlist";
}
#[derive(Debug)]
pub struct User;
impl ResourceTypes for User {
    const NAME: &'static str = "user";
}

#[derive(Debug)]
pub struct GenericResourceIdentifier<R>
where
    R: ResourceTypes,
{
    pub id: String,
    resource_type: PhantomData<R>,
}

impl<R: ResourceTypes> GenericResourceIdentifier<R> {
    pub fn new(identifier: &str) -> Result<GenericResourceIdentifier<R>> {
        ensure!(vec![ID_REGEX, URI_REGEX, URL_REGEX]
            .into_iter()
            .try_fold(false, |acc, x| {
                match Regex::new(x) {
                    Ok(r) => Ok(acc || r.is_match(&identifier)),
                    Err(e) => Err(e),
                }
            })?);

        let id = match Regex::new(r"[0-9A-Za-z]{22,28}")?
            .captures(&identifier)
            .and_then(|c| c.get(0))
            .map(|c| c.as_str().to_string())
        {
            Some(i) => i,
            None => bail!("Invalid identifier"),
        };

        Ok(GenericResourceIdentifier {
            id,
            resource_type: PhantomData,
        })
    }

    pub fn id(&self) -> String {
        self.id.clone()
    }

    pub fn uri(&self) -> String {
        format!("spotify:{}:{}", R::NAME, self.id)
    }

    pub fn url(&self) -> String {
        format!("https://open.spotify.com/{}/{}", R::NAME, self.id)
    }
}

impl UserID {
    pub async fn get(token: &AccessToken) -> Result<UserID> {
        let response: serde_json::Value = serde_json::from_str(
            &reqwest::Client::new()
                .get("https://api.spotify.com/v1/me")
                .header(
                    AUTHORIZATION,
                    HeaderValue::from_str(&format!("Bearer {}", token.access_token))?,
                )
                .send()
                .await?
                .text()
                .await?,
        )?;

        dbg!(&response);

        match response.get("uri") {
            Some(i) => {
                let id = i.as_str().unwrap();
                println!("{id}");
                Ok(UserID::new(id)?)
            }
            None => bail!("Unable to get user ID"),
        }
    }
}
