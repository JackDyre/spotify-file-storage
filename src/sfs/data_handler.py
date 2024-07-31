"""Uploads/download data of arbitrary size to Spotify playlist."""

import json
from base64 import b64decode, b64encode
from itertools import batched

from .encryption import decrypt, encrypt
from .playlistmanager import download_bytes, upload_bytes
from .requestmanager import sp

PLAYLIST_DATA_SIZE = 19_950


def upload_data(data: bytes, header: dict, key: str) -> str:
    """
    Encrypt and upload data of arbitrary size to Spotify playlist(s).

    :param data: The bytes object to be broken up an uploaded.
    :param header: Any metadata to go along with the data (such as the filename).
    """
    base64_data = b64encode(data).decode("utf-8")
    playlist_batches = [
        "".join(batch) for batch in batched(base64_data, PLAYLIST_DATA_SIZE)
    ]

    playlist_count = len(playlist_batches)

    playlist_ids = []
    for _ in range(playlist_count):
        title = b64encode(encrypt(pad(key.encode("utf-8"), 50), key=key)).decode(
            "utf-8"
        )
        description = b64encode(
            encrypt(pad(title.encode("utf-8"), 100), key=key)
        ).decode("utf-8")
        playlist_ids.append(
            sp.send_request(
                endpoint=sp.user_playlist_create,
                user=sp.current_user()["id"],
                name=title,
                description=description,
            )["id"]
        )

    next_ids = playlist_ids[1:] + [None]

    playlist_dicts = [{} for _ in range(playlist_count)]

    for i, playlist_dict in enumerate(playlist_dicts):
        playlist_dict["content"] = playlist_batches[i]
        if next_ids[i]:
            playlist_dict["next"] = next_ids[i]
        if i == 0:
            playlist_dict.update(header)

    encrypted_batches = [
        encrypt(
            pad(json.dumps(playlist_dict).encode("utf-8"), size=PLAYLIST_DATA_SIZE),
            key=key,
        )
        for playlist_dict in playlist_dicts
    ]

    for i, batch in enumerate(encrypted_batches):
        upload_bytes(batch, playlist_ids[i])

    return playlist_ids[0]


def download_data(playlist_id: str, key: str) -> tuple[dict, bytes]:
    """
    Fetch all data iteratively starting from a provided playlist.

    :param playlist_id: The ID of the first playlist that stores the data.
    :param key: The encryption key.
    """
    data = json.loads(
        unpad(decrypt(download_bytes(playlist_id), key=key)).decode("utf-8")
    )
    header = {k: v for k, v in data.items() if k not in ["content", "next"]}
    content = data["content"]

    if "next" in data:
        while True:
            next_id = data["next"]
            data = json.loads(
                unpad(decrypt(download_bytes(next_id), key=key)).decode("utf-8")
            )
            content += data["content"]
            if "next" not in data:
                break

    return header, b64decode(content).decode("utf-8")


def pad(data: bytes, size: int) -> bytes:
    """Pad data with null bytes."""
    if len(data) > size - 2:
        raise ValueError

    pad_size = size - 2 - len(data)

    return (pad_size + 2).to_bytes(2, byteorder="big") + b"\0" * pad_size + data


def unpad(data: bytes) -> bytes:
    """Un-pad data."""
    data_start = data[0] * 256 + data[1]

    return data[data_start:]


def main() -> None:
    """Run main logic."""
