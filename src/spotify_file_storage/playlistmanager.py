"""Handles the upload/download of binary objects to and from Spotify playlists."""

from itertools import batched

import polars as pl

from spotify_file_storage.requestmanager import sp

binary_to_id = pl.read_json("src/spotify_file_storage/json/binarytoid.json")
identifier_to_binary = pl.read_json(
    "src/spotify_file_storage/json/identifiertobinary.json"
)

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
                binary_to_id[byte].to_list()[0] for byte in one_byte_string
            )
        else:
            two_byte_val = 256 * batch[0] + batch[1]
            track_ids.append(binary_to_id[bin(two_byte_val)[2:].zfill(16)].to_list()[0])

    if len(track_ids) > MAX_PLAYLIST_SIZE:
        raise ValueError

    batched_track_ids = batched(track_ids, 100)
    print(*batched_track_ids)
    for batch in batched_track_ids:
        sp.send_request(
            endpoint=sp.user_playlist_add_tracks,
            user=sp.current_user,
            playlist_id=playlist_id,
            tracks=list(batch),
        )


def main() -> None:
    """Run main logic."""


if __name__ == "__main__":
    main()
