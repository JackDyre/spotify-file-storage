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


REQUEST_RATE_LIMIT = os.getenv("REQUEST_RATE_LIMIT") or 0


_recent_request_time = time.time()


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


def create_client() -> spotipy.Spotify:
    """
    Create a Spotify client session using API credentials from environment variables.

    Run `source ./apikeys.sh` to set API credentials in the environment variables.

    :return: A Spotify client session
    """
    if not ("CLIENT_ID" in os.environ and "CLIENT_SECRET" in os.environ):
        raise APICredentialsNotFoundError

    client_id = os.getenv("CLIENT_ID")
    client_secret = os.getenv("CLIENT_SECRET")

    return spotipy.Spotify(
        auth_manager=SpotifyOAuth(
            client_id=client_id,
            client_secret=client_secret,
            scope=" ".join(SCOPES),
            redirect_uri="http://localhost:8888/callback",
        )
    )


sp = create_client()


def send_request(endpoint: Callable, *args: str | list, **kwargs: str | list) -> dict:
    """
    Handle rate-limiting logic regarding sending a request to Spotify's Web API.

    :param endpoint: An endpoint method from spotipy.Spotify
    :param args: Args to be passed into the endpoint.
    :param kwargs: Kwargs to be passed into the enpoint.
    :return: The response from Spotify's Web API.
    """
    global _recent_request_time

    current_time = time.time()
    if current_time - _recent_request_time < REQUEST_RATE_LIMIT:
        time.sleep(REQUEST_RATE_LIMIT + _recent_request_time - current_time)

    _recent_request_time = current_time

    return endpoint(*args, **kwargs)


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
    _ = send_request(
        sp.playlist,
        "4",
        playlist_id="https://open.spotify.com/playlist/5xNvpxP9MuBWshF8QdbrmF?si=f5a63f5c8c5c4ffc",
    )


if __name__ == "__main__":
    main()
