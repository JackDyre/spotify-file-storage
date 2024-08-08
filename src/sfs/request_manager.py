"""Handles logic for sending requests to Spotify's Web API."""

import os
import time
from collections.abc import Callable

import spotipy
from spotipy.oauth2 import SpotifyOAuth

SCOPES = [
    "playlist-read-private",
    "playlist-modify-public",
    "playlist-modify-private",
]


REQUEST_RATE_LIMIT = float(os.getenv("REQUEST_RATE_LIMIT") or 0)


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


class SpotifyClient(spotipy.Spotify):
    """A wrapper for spotipy.Spotify that handles rate limiting client-side."""

    def __init__(self) -> None:
        """Initialize instance as a subclass of spotify.Spotify."""
        if not ("CLIENT_ID" in os.environ and "CLIENT_SECRET" in os.environ):
            raise APICredentialsNotFoundError

        self._client_id = os.getenv("CLIENT_ID")
        self._client_secret = os.getenv("CLIENT_SECRET")

        super().__init__(
            auth_manager=SpotifyOAuth(
                client_id=self._client_id,
                client_secret=self._client_secret,
                scope=" ".join(SCOPES),
                redirect_uri="http://localhost:8888/callback",
            )
        )

        self._recent_request_time = time.time()

    def send_request(
        self, endpoint: Callable, *args: str | list | dict, **kwargs: str | list | dict
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
    playlist_tracks: list[dict] = []

    playlist: dict = {}

    while True:
        playlist = (
            sp.send_request(sp.playlist_items, playlist_id)
            if not playlist_tracks
            else sp.send_request(sp.next, playlist)
        )
        playlist_tracks.extend(track["track"] for track in playlist["items"])
        if playlist["next"] is None:
            break

    return playlist_tracks
