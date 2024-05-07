import gzip as gz
import os
import sqlite3
import tkinter as tk
from math import ceil
from tkinter import filedialog
from sqlite3 import Connection, Cursor

import pyperclip  # type: ignore

from main import (api_request_manager, batch, decimal_to_binary_padded,
                  print_progress_bar)
from typing import Generator


class File:
    def __init__(self, file_path: str) -> None:
        self.path: str = file_path
        self.name: str = os.path.basename(file_path)
    
    @property
    def compressed_binary(self) -> list[int]:
        with open(self.path, 'rb') as f:
            with gz.open('temp_archive.gz', 'wb') as temp_archive:
                temp_archive.writelines(f)

        with open('temp_archive.gz', "rb") as f:  # type: ignore
            file_bytes = list(f.read())
        
        os.remove('temp_archive.gz')

        return self.bytes_to_binary(file_bytes)
    
    @property
    def uncompressed_binary(self) -> list[int]:
        with open(self.path, 'rb') as f:
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

def get_binary(file: File, is_compressed: bool=True) -> list[int]:
    if is_compressed:
        return file.compressed_binary
    else:
        return file.uncompressed_binary

def confirmation_prompt() -> bool:
    raise NotImplementedError

def split_binary_into_tracks(binary: list, bits_per_track: int, cursor: Cursor) -> Generator:
    for track_data in batch(binary, bits_per_track):
        if len(track_data) == bits_per_track:
            yield lookup_id_in_db(track_data, cursor)
        else:
            for byte in track_data:
                yield lookup_id_in_db(byte, cursor)

def lookup_id_in_db(binary: list, cursor: Cursor) -> str:
    cursor.execute(
                "SELECT * FROM _13bit_ids WHERE binary = ?", (str(binary),)
            )
    track_id = cursor.fetchall()[0][1]
    return track_id

def w(file: File, is_compressed: bool=True, lookup_db: str='13bit_ids.db', max_tracks_per_playlist: int=9_988, bits_per_track: int = 13, print_progress: bool=True, confirm_write: bool=True) -> str | None:

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
    for idx, playlist_batch in enumerate(batch(split_binary_into_tracks(file_binary, bits_per_track, db_cursor), max_tracks_per_playlist), start=1):
        
        playlist_id = api_request_manager.send_request(
            api_request_manager.sp.user_playlist_create,
            user=api_request_manager.user_id,
            name=f"{file.name}: Playlist {idx} of {playlist_count}",
        )["id"]
        playlist_ids.append(playlist_id)

        api_request_manager.add_tracks_to_playlist(playlist=playlist_id, tracks=list(playlist_batch))
    
    header_string = "*".join([file.name] + playlist_ids)
    header_tracks = split_binary_into_tracks(File.bytes_to_binary(list(header_string.encode('utf-8'))), bits_per_track, db_cursor)

    header_id = api_request_manager.send_request(
        api_request_manager.sp.user_playlist_create,
        user=api_request_manager.user_id,
        name=f"{file.name}: Header Playlist",
    )["id"]

    api_request_manager.add_tracks_to_playlist(playlist=header_id, tracks=list(header_tracks))

    return header_id







def write_file_to_playlist(file) -> str | None:
    filename = os.path.basename(file)


    with open(file, 'rb') as uncompressed_file:
        with gz.open(f'{filename}.gz', 'wb') as compressed_file:
            compressed_file.writelines(uncompressed_file)

    with open(f'{filename}.gz', "rb") as f:  # type: ignore
        file_bytes = list(f.read())
    
    os.remove(f'{filename}.gz')

    file_binary: list = []
    for idx, byte in enumerate(file_bytes):
        print_progress_bar(idx, len(file_bytes))
        file_binary.extend(decimal_to_binary_padded(byte, 8))

    conn = sqlite3.connect("13bit_ids.db")
    cursor = conn.cursor()

    song_count = (len(file_binary) // 13) + (len(file_binary) % 13)
    playlist_count = ceil(song_count / 9_975)

    print(
        f"\n\nFile: {filename}\nRequires ~{ceil(song_count // 100)} API requests\nTime estimate: {round(ceil(song_count // 100) * .75, 0)}sec"
    )

    continue_check = input("Confirm? (Y/N) ")
    if not (continue_check == "Y" or continue_check == "y"):
        return None

    print(f"\n\nDumping {song_count} tracks into {playlist_count} playlists...\n\n")

    playlist_ids: list = []
    playlist_iter = 0
    for playlist_data in batch(file_binary, 9_975 * 13):

        track_ids: list = []

        playlist_iter += 1
        playlist_id = api_request_manager.send_request(
            api_request_manager.sp.user_playlist_create,
            user=api_request_manager.user_id,
            name=f"{filename}: Playlist {playlist_iter} of {playlist_count}",
        )["id"]
        playlist_ids.append(playlist_id)

        for track_data in batch(playlist_data, 13):
            if len(track_data) == 13:
                cursor.execute(
                    "SELECT * FROM _13bit_ids WHERE binary = ?", (str(track_data),)
                )
                track_id = cursor.fetchall()
                track_ids.append(track_id[0][1])
            else:
                for byte in track_data:
                    cursor.execute(
                        "SELECT * FROM _13bit_ids WHERE binary = ?", (str(byte),)
                    )
                    track_id = cursor.fetchall()
                    track_ids.append(track_id[0][1])

        print(f"Dumping tracks to playlist {playlist_iter} of {playlist_count}...")
        print(f"Playlist size: {len(track_ids)}\n")
        api_request_manager.add_tracks_to_playlist(playlist_id, track_ids)

    header_playlist = api_request_manager.send_request(
        request=api_request_manager.sp.user_playlist_create,
        user=api_request_manager.user_id,
        name=f"{filename}: Header Playlist",
    )["id"]
    header_string = "*".join([filename] + playlist_ids)
    header_bytes = list(header_string.encode("utf-8"))

    header_binary = []
    for idx, byte in enumerate(header_bytes):
        header_binary.extend(decimal_to_binary_padded(byte, 8))

    header_track_ids: list = []
    for header_track_data in batch(header_binary, 13):
        if len(header_track_data) == 13:
            cursor.execute(
                "SELECT * FROM _13bit_ids WHERE binary = ?",
                (str(header_track_data),),
            )
            track_id = cursor.fetchall()
            header_track_ids.append(track_id[0][1])
        else:
            for byte in header_track_data:
                cursor.execute(
                    "SELECT * FROM _13bit_ids WHERE binary = ?", (str(byte),)
                )
                track_id = cursor.fetchall()
                header_track_ids.append(track_id[0][1])

    print(f"Dumping tracks to header playlist...")
    print(f"Header size: {len(header_track_ids)}")
    api_request_manager.add_tracks_to_playlist(header_playlist, header_track_ids)

    cursor.close()
    conn.close()
    return header_playlist


if __name__ == '__main__':
    file = File(get_file_path())
    header_playlist = w(file, confirm_write=False, print_progress=False)
    pyperclip.copy(header_playlist)
    print('\nHeader playlist ID copied to clipboard')