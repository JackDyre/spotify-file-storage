"""Handles the upload/download of binary objects to and from Spotify playlists."""

from collections.abc import Sequence, Sized
from typing import TypeVar

from requestmanager import sp

T = TypeVar("T", bound=list | bytes)


def batch(seq: T, size: int) -> list[T]:
    for i in range(len(seq)):
        ...


def upload_bytes(_: bytes) -> str:
    """Upload a bytes object to Spotify and return the ID of the first playlist."""


def main() -> None:
    """Run main logic."""
    # print(*batch(b"what is up motherfucker i am going to kill you", 2), sep='\n')
    print(*batch(tuple(range(7)), 2), sep="\n")


if __name__ == "__main__":
    main()
