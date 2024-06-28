from collections.abc import Callable
from typing import Any
import json

import spotipy
from spotipy.oauth2 import SpotifyOAuth


def create_client(api_credentials: dict) -> spotipy.Spotify:
    assert "client_id" in api_credentials.keys()
    assert "client_secret" in api_credentials.keys()

    client_id = api_credentials["client_id"]
    client_secret = api_credentials["client_secret"]

    sp = spotipy.Spotify(
        auth_manager=SpotifyOAuth(
            client_id=client_id,
            client_secret=client_secret,
            scope="playlist-read-private playlist-modify-public playlist-modify-private",
            redirect_uri="http://localhost:8888/callback",
        )
    )

    return sp


with open("api-credentials.json", "r") as f:
    sp = create_client(json.load(f))


def send_request(endpoint: Callable, **kwargs) -> Any:
    response = endpoint(**kwargs)
    return response


def get_playlist_tracks(playlist_id: str) -> list[dict]:
    play_list_tracks = list()

    playlist: dict = sp.playlist_items(playlist_id)
    play_list_tracks.extend(playlist["items"])

    while playlist["next"]:
        playlist: dict = sp.next(playlist)
        play_list_tracks.extend(playlist["items"])

    return play_list_tracks


def add_playlist_tracks(tracks: list[str], playlist_id: str) -> dict:
    pass


get_playlist_tracks(
    "https://open.spotify.com/playlist/4uz1h3jAKkoH3nZKUnrehK?si=675120a52b8c46cd"
)
