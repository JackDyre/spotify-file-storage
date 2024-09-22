use anyhow::bail;
use anyhow::Result;
use regex::Regex;
use reqwest::header::{HeaderValue, AUTHORIZATION};
use serde::Deserialize;
use std::marker::PhantomData;

use crate::auth::AccessToken;

#[derive(Debug, Deserialize)]
pub struct UserID {
    pub id: String,
}

impl UserID {
    pub async fn new(token: &AccessToken) -> Result<UserID> {
        let response: UserID = serde_json::from_str(
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

        Ok(response)
    }
}

pub trait IdTypes {
    const NAME: &'static str;
    const REGEX: &'static str;
}
pub trait ResourceTypes {
    const NAME: &'static str;
}

pub struct ID;
impl IdTypes for ID {
    const NAME: &'static str = "ID";
    const REGEX: &'static str = r"^[0-9A-Za-z]{22}$";
}
pub struct URI;
impl IdTypes for URI {
    const NAME: &'static str = "URI";
    const REGEX: &'static str = r"^spotify:(track|playlist|user):([0-9A-Za-z]{22})$";
}
pub struct URL;
impl IdTypes for URL {
    const NAME: &'static str = "URL";
    const REGEX: &'static str = r"^https:\/\/open\.spotify\.com\/(track|playlist|user)\/([0-9A-Za-z]{22})(\?si=[0-9A-Za-z]+)?$";
}

pub struct Track;
impl ResourceTypes for Track {
    const NAME: &'static str = "track";
}
pub struct Playlist;
impl ResourceTypes for Playlist {
    const NAME: &'static str = "playlist";
}
pub struct User;
impl ResourceTypes for User {
    const NAME: &'static str = "user";
}

pub struct ResourceIdentifier<I, R>
where
    I: IdTypes,
    R: ResourceTypes,
{
    pub identifier: String,
    _id_type: PhantomData<I>,
    _resource_type: PhantomData<R>,
}

impl<I, R> ResourceIdentifier<I, R>
where
    I: IdTypes,
    R: ResourceTypes,
{
    pub fn new(identifier: &str) -> Result<ResourceIdentifier<I, R>> {
        let regex = Regex::new(I::REGEX)?;

        if !regex.is_match(&identifier) {
            bail!("Invalid {} {}: {}", R::NAME, I::NAME, identifier)
        }

        Ok(Self {
            identifier: identifier.to_string(),
            _id_type: PhantomData,
            _resource_type: PhantomData,
        })
    }
}
