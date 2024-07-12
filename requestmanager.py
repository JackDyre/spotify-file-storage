import os
from collections.abc import Callable
from typing import Any

import spotipy
from spotipy.oauth2 import SpotifyOAuth


def create_client() -> spotipy.Spotify:
    """
    Create a Spotify client session using API credentials from environment variables.

    Run `source ./apikeys.sh` to set API credentials in the environment variables.

    :return: A Spotify client session
    """
    assert (
        "CLIENT_ID" in os.environ and "CLIENT_SECRET" in os.environ
    ), "You must set API credentials environment variables before running this.\n\n`source ./apikeys.sh`"

    client_id = os.getenv("CLIENT_ID")
    client_secret = os.getenv("CLIENT_SECRET")

    return spotipy.Spotify(
        auth_manager=SpotifyOAuth(
            client_id=client_id,
            client_secret=client_secret,
            scope="playlist-read-private playlist-modify-public playlist-modify-private",
            redirect_uri="http://localhost:8888/callback",
        )
    )


sp = create_client()


def send_request(endpoint: Callable, **kwargs: Any) -> Any:
    # TODO(Jack Dyre): Request rate limiting
    return endpoint(**kwargs)


def get_playlist_tracks(playlist_id: str) -> list[dict]:
    play_list_tracks = []

    playlist: dict = sp.playlist_items(playlist_id)
    play_list_tracks.extend(playlist["items"])

    while playlist["next"]:
        playlist: dict = sp.next(playlist)
        play_list_tracks.extend(playlist["items"])

    return play_list_tracks
