import gzip as gz
import os
import sqlite3
import tkinter as tk
from math import ceil
from sqlite3 import Connection, Cursor
from tkinter import filedialog
from typing import Generator

import pyperclip  # type: ignore

from main import (
    api_request_manager,
    batch,
    decimal_to_binary_padded,
    print_progress_bar,
)


class File:
    def __init__(self, file_path: str) -> None:
        self.path: str = file_path
        self.name: str = os.path.basename(file_path)

    @property
    def compressed_binary(self) -> list[int]:
        with open(self.path, "rb") as f:
            with gz.open("temp_archive.gz", "wb") as temp_archive:
                temp_archive.writelines(f)

        with open("temp_archive.gz", "rb") as f:  # type: ignore
            file_bytes = list(f.read())

        os.remove("temp_archive.gz")

        return self.bytes_to_binary(file_bytes)

    @property
    def uncompressed_binary(self) -> list[int]:
        with open(self.path, "rb") as f:
            file_bytes = list(f.read())

        return self.bytes_to_binary(file_bytes)

    @staticmethod
    def bytes_to_binary(bytes: list[int]) -> list[int]:
        binary: list[int] = []
        for byte in bytes:
            binary.extend(decimal_to_binary_padded(byte, 8))

        return binary


def get_file_path():
    root = tk.Tk()
    root.withdraw()
    return filedialog.askopenfilename()


def get_binary(file: File, is_compressed: bool = True) -> list[int]:
    if is_compressed:
        return file.compressed_binary
    else:
        return file.uncompressed_binary


def confirmation_prompt() -> bool:
    raise NotImplementedError


def split_binary_into_tracks(
    binary: list, bits_per_track: int, cursor: Cursor
) -> Generator:
    for track_data in batch(binary, bits_per_track):
        if len(track_data) == bits_per_track:
            yield lookup_id_in_db(track_data, cursor)
        else:
            for byte in track_data:
                yield lookup_id_in_db(byte, cursor)


def lookup_id_in_db(binary: list, cursor: Cursor) -> str:
    cursor.execute("SELECT * FROM _13bit_ids WHERE binary = ?", (str(binary),))
    track_id = cursor.fetchall()[0][1]
    return track_id


def write_to_playlist(
    file: File,
    is_compressed: bool = True,
    lookup_db: str = "13bit_ids.db",
    max_tracks_per_playlist: int = 9_988,
    bits_per_track: int = 13,
    print_progress: bool = True,
    confirm_write: bool = True,
) -> str | None:

    file_binary: list[int] = get_binary(file=file, is_compressed=is_compressed)

    db_connection: Connection = sqlite3.connect(lookup_db)
    db_cursor: Cursor = db_connection.cursor()

    track_count = len(file_binary) // 13 + len(file_binary) % 13
    playlist_count = ceil(track_count / max_tracks_per_playlist)

    if confirm_write and confirmation_prompt():
        return None

    if print_progress:
        raise NotImplementedError

    playlist_ids: list[str] = []
    for idx, playlist_batch in enumerate(
        batch(
            split_binary_into_tracks(file_binary, bits_per_track, db_cursor),
            max_tracks_per_playlist,
        ),
        start=1,
    ):

        playlist_id = api_request_manager.send_request(
            api_request_manager.sp.user_playlist_create,
            user=api_request_manager.user_id,
            name=f"{file.name}: Playlist {idx} of {playlist_count}",
        )["id"]
        playlist_ids.append(playlist_id)

        api_request_manager.add_tracks_to_playlist(
            playlist=playlist_id, tracks=list(playlist_batch)
        )

    header_string = "*".join([file.name] + playlist_ids)
    header_tracks = split_binary_into_tracks(
        File.bytes_to_binary(list(header_string.encode("utf-8"))),
        bits_per_track,
        db_cursor,
    )

    header_id = api_request_manager.send_request(
        api_request_manager.sp.user_playlist_create,
        user=api_request_manager.user_id,
        name=f"{file.name}: Header Playlist",
    )["id"]

    api_request_manager.add_tracks_to_playlist(
        playlist=header_id, tracks=list(header_tracks)
    )

    db_cursor.close()
    db_connection.close()

    return header_id


if __name__ == "__main__":
    file = File(get_file_path())
    header_playlist = write_to_playlist(file, confirm_write=False, print_progress=False)
    pyperclip.copy(header_playlist)
    print("\nHeader playlist ID copied to clipboard")
