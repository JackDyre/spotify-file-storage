use thiserror::Error;

#[derive(Error, Debug)]
pub enum AuthError {
    #[error("The captured callback url was malformed")]
    InvalidCallback,
    #[error("Authorization callback returned an error")]
    DuringAuthorization,
    #[error("State sent to Spotify does not match the one returned")]
    MismatchedStates,
}
