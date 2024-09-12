use thiserror::Error;

#[derive(Error, Debug)]
#[error("{msg}")]
pub struct SfsError {
    msg: String,
}

impl SfsError {
    pub fn new(msg: &str) -> SfsError {
        SfsError {
            msg: msg.to_string(),
        }
    }

    pub fn new_box(msg: &str) -> Box<SfsError> {
        Box::new(SfsError::new(msg))
    }
}
