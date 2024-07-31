"""Handles the upload/download of bytes objects to single Spotify playlists."""

from itertools import batched

import polars as pl

from .requestmanager import get_playlist_tracks, sp

BINARY_TO_ID = pl.read_json("src/sfs/json/binary_to_id.json")
IDENTIFIER_TO_BINARY = pl.read_json("src/sfs/json/identifier_to_binary.json")

MAX_PLAYLIST_SIZE = 10_000


def upload_bytes(data: bytes, playlist_id: str) -> None:
    """
    Upload a bytes object to a Spotify playlist.

    :param data: A bytes object to be written.
    :param playlist_id: A string of the playlist ID to write the bytes to.
    """
    batched_data = batched(data, 2)

    track_ids = []

    for batch in batched_data:
        if len(batch) == 1:
            one_byte_string = bin(batch[0])[2:].zfill(8)
            track_ids.extend(
                BINARY_TO_ID[byte].to_list()[0] for byte in one_byte_string
            )
        else:
            two_byte_val = 256 * batch[0] + batch[1]
            track_ids.append(BINARY_TO_ID[bin(two_byte_val)[2:].zfill(16)].to_list()[0])

    if len(track_ids) > MAX_PLAYLIST_SIZE:
        raise ValueError

    batched_track_ids = batched(track_ids, 100)
    for batch in batched_track_ids:
        sp.send_request(
            endpoint=sp.user_playlist_add_tracks,
            user=sp.current_user,
            playlist_id=playlist_id,
            tracks=list(batch),
        )


def download_bytes(playlist_id: str) -> bytes:
    """
    Retrieve data from the specified playlist.

    :param playlist_id: The ID of the playlist.
    :return: A bytes object of the retrieved data.
    """
    tracks_identifiers = (
        "||".join(
            [
                f"{t['duration_ms']}",
                t["external_ids"]["isrc"],
                t["name"],
                t["album"]["name"],
                t["album"]["images"][0]["url"],
            ]
        )
        for t in get_playlist_tracks(playlist_id)
    )

    binary_string = ""

    for identifier in tracks_identifiers:
        binary_string += IDENTIFIER_TO_BINARY[identifier].to_list()[0]

    return bytes(
        int(binary_string[i : i + 8], 2) for i in range(0, len(binary_string), 8)
    )
