#[derive(Debug)]
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

impl std::fmt::Display for SfsError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "{}", self.msg)
    }
}

impl std::error::Error for SfsError {}
