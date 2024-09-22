use anyhow::{anyhow, bail, ensure, Result};
use regex::{Regex, RegexSet};
use reqwest::header::{HeaderValue, AUTHORIZATION};
use std::marker::PhantomData;
use std::sync::LazyLock;

use crate::spotify::auth::AccessToken;

pub type UserID = GenericResourceIdentifier<User>;
pub type PlaylistID = GenericResourceIdentifier<Playlist>;
pub type TrackID = GenericResourceIdentifier<Track>;

static IDENTIFIER_REGEX_SET: LazyLock<RegexSet> = LazyLock::new(|| {
    RegexSet::new(vec![
        r"^[0-9A-Za-z]{22,28}$",
        r"^spotify:(track|playlist|user):([0-9A-Za-z]{22,28})$",
        r"^https:\/\/open\.spotify\.com\/(track|playlist|user)\/([0-9A-Za-z]{22,28})(\?si=[0-9A-Za-z]+)?$",
    ]).expect("ID validitation regexes should be valid")
});
static ID_REGEX: LazyLock<Regex> = LazyLock::new(|| {
    Regex::new(r"[0-9A-Za-z]{22,28}").expect("ID validitation regexes should be valid")
});

pub trait ResourceTypes {
    const NAME: &'static str;
}
#[derive(Debug)]
#[doc(hidden)]
pub struct Track;
impl ResourceTypes for Track {
    const NAME: &'static str = "track";
}
#[derive(Debug)]
#[doc(hidden)]
pub struct Playlist;
impl ResourceTypes for Playlist {
    const NAME: &'static str = "playlist";
}
#[derive(Debug)]
#[doc(hidden)]
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
        ensure!(IDENTIFIER_REGEX_SET.is_match(&identifier));

        let id = match ID_REGEX
            .find(&identifier)
            .map(|mat| mat.as_str().to_string())
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

        match response.get("uri") {
            Some(i) => Ok(UserID::new(
                i.as_str().ok_or_else(|| anyhow!("Unable to get user ID"))?,
            )?),
            None => bail!("Unable to get user ID"),
        }
    }
}
