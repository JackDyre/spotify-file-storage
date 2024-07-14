"""Handles logic for sending requests to Spotify's Web API."""

import os
import time
from collections.abc import Callable
from typing import TypeVar

import spotipy
from spotipy.oauth2 import SpotifyOAuth

SCOPES = [
    "playlist-read-private",
    "playlist-modify-public",
    "playlist-modify-private",
]


REQUEST_RATE_LIMIT = os.getenv("REQUEST_RATE_LIMIT") or 0


class APICredentialsNotFoundError(Exception):
    """Error raised when API credentials can not be found."""

    def __init__(self) -> None:
        """Initialize the error."""
        super().__init__("""
        -----
        API credentials environment variables not found.
        Please run `source ./apikeys.sh` before running this.
        -----
        """)


class SpotifyClient:
    """A wrapper for spotipy.Spotify that handles rate limiting client-side."""

    T = TypeVar("T")

    def __init__(self) -> None:
        """Initialize instance with spotify.Spotify instance."""
        if not ("CLIENT_ID" in os.environ and "CLIENT_SECRET" in os.environ):
            raise APICredentialsNotFoundError

        self._client_id = os.getenv("CLIENT_ID")
        self._client_secret = os.getenv("CLIENT_SECRET")

        self.sp = spotipy.Spotify(
            auth_manager=SpotifyOAuth(
                client_id=self._client_id,
                client_secret=self._client_secret,
                scope=" ".join(SCOPES),
                redirect_uri="http://localhost:8888/callback",
            )
        )

        self._recent_request_time = time.time()

    def __getattr__(self, attr: str) -> T:
        """Pass attr queries through to self.sp to make use easier."""
        if hasattr(self.sp, attr):
            return getattr(self.sp, attr)

        raise AttributeError

    def send_request(
        self, endpoint: Callable, *args: str | list, **kwargs: str | list
    ) -> dict:
        """
        Handle rate-limiting logic regarding sending a request to Spotify's Web API.

        :param endpoint: An endpoint method from spotipy.Spotify
        :param args: Args to be passed into the endpoint.
        :param kwargs: Kwargs to be passed into the enpoint.
        :return: The response from Spotify's Web API.
        """
        current_time = time.time()
        if current_time - self._recent_request_time < REQUEST_RATE_LIMIT:
            time.sleep(REQUEST_RATE_LIMIT + self._recent_request_time - current_time)

        self._recent_request_time = current_time

        return endpoint(*args, **kwargs)


sp = SpotifyClient()


def get_playlist_tracks(playlist_id: str) -> list[dict]:
    """
    Fetch all tracks in a playlist.

    :param playlist_id: The playlist ID, URL, or URI.
    :return: A list of dictionaries containing info about each track.
    """
    play_list_tracks = []

    playlist: dict = sp.playlist_items(playlist_id)
    play_list_tracks.extend(playlist["items"])

    while playlist["next"]:
        playlist: dict = sp.next(playlist)
        play_list_tracks.extend(playlist["items"])

    return play_list_tracks


def main() -> None:
    """Run the main logic for the program."""


if __name__ == "__main__":
    main()
