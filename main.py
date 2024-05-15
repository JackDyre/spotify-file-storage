﻿import gzip as gz
import hashlib
import json
import os
import pickle
import sqlite3
import sys
import time
import tkinter as tk
from math import ceil
from sqlite3 import Cursor
from tkinter import filedialog
from typing import Iterable

import pyperclip
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials, SpotifyOAuth


def print_progress_bar(iteration: int, total: int):
    percent = "{0:.1f}".format(100 * ((iteration + 1) / float(total)))
    filled_length = int(50 * (iteration + 1) // total)
    bar = "X" * filled_length + "-" * (50 - filled_length)
    print(f"\r|{bar}| {percent}%", end="")
    if iteration + 1 == total:
        print()


def decimal_to_binary_padded(decimal, pad):
    binary = bin(decimal)[2:]
    return [int(bit) for bit in binary.zfill(pad)]


def batch(iterable, batch_size):
    iterator = iter(iterable)
    while True:
        batch_list = []
        for _ in range(batch_size):
            try:
                batch_list.append(next(iterator))
            except StopIteration:
                break
        if not batch_list:
            break
        yield batch_list


def open_file_dialog(dialog_type: str) -> str:
    root = tk.Tk()
    root.withdraw()
    if dialog_type == "directory":
        return filedialog.askdirectory()
    if dialog_type == "file":
        return filedialog.askopenfilename()
    raise ValueError("Invalid filedialog type")


def binary_bytes_conversion(
        binary: Iterable | list[int], conversion_type: str
) -> list[int]:
    if conversion_type == "binary_to_bytes":
        return list(
            bytearray(int("".join(map(str, byte)), 2) for byte in batch(binary, 8))
        )
    elif conversion_type == "bytes_to_binary":
        return [
            int(bit) for byte in bytearray(binary) for bit in bin(byte)[2:].zfill(8)
        ]
    raise ValueError(
        "Invalid conversion type. Valid types are: 'binary_to_bytes' and 'bytes_to_binary'"
    )


def db_query(
        output_column: str, reference_column: str, query: str, table: str, cursor: Cursor
) -> str:
    cursor.execute(
        f"SELECT {output_column} FROM {table} WHERE {reference_column} = ?", (query,)
    )
    return cursor.fetchone()[0]


class APIRequests:
    def __init__(self) -> None:
        self.recent_request: float = time.time()
        self.sp: spotipy.Spotify = self.create_client()
        self.user_id: str = self.send_request(request=self.sp.current_user)["id"]

    @staticmethod
    def create_client() -> spotipy.Spotify:
        try:
            with open("api-credentials.json", "r") as f:
                api_dict = json.load(f)
            client_id = api_dict["cl-id"]
            client_secret = api_dict["cl-secret"]
        except FileNotFoundError:
            client_id = input("Client ID?\n")
            client_secret = input("Client Secret?\n")
            with open("api-credentials.json", "w") as f:
                json.dump(obj={"cl-id": client_id, "cl-secret": client_secret}, fp=f)

        try:
            spotipy.Spotify(
                client_credentials_manager=SpotifyClientCredentials(
                    client_id=client_id, client_secret=client_secret
                ),
            )
        except spotipy.SpotifyException:
            os.remove("api-credentials.json")
            print("\n\nInvalid API info")
            sys.exit()

        sp: spotipy.Spotify = spotipy.Spotify(
            client_credentials_manager=SpotifyClientCredentials(
                client_id=client_id, client_secret=client_secret
            ),
            auth_manager=SpotifyOAuth(
                client_id=client_id,
                client_secret=client_secret,
                scope="playlist-read-private playlist-modify-public playlist-modify-private",
                redirect_uri="http://localhost:8888/callback",
            ),
            retries=0,
        )
        return sp

    def get_playlist_tracks(
            self, playlist: str, print_progress: bool = True
    ) -> list[dict]:
        offset: int = 0
        tracks: list[dict] = []
        playlist_len: int = api_request_manager.send_request(
            request=api_request_manager.sp.playlist, playlist_id=playlist
        )["tracks"]["total"]
        while True:
            track_batch = self.send_request(
                request=self.sp.playlist_items,
                playlist_id=playlist,
                offset=offset,
                market="US",
            )
            offset += 100
            if print_progress:
                print_progress_bar(offset, playlist_len)
            for track in track_batch["items"]:
                tracks.append(track["track"])
            if not track_batch["next"]:
                break
        return tracks

    def add_tracks_to_playlist(
            self, playlist: str, tracks: list[str], print_progress: bool = False
    ) -> None:
        for idx, track_batch in enumerate(batch(tracks, 100)):
            if print_progress:
                print_progress_bar(idx, len(list(batch(tracks, 100))))
            self.send_request(
                request=self.sp.playlist_add_items,
                playlist_id=playlist,
                items=track_batch,
            )

    def get_user_playlists(self) -> list[dict]:
        playlists: list[dict] = []
        offset = 0
        while True:
            playlist_batch = self.send_request(
                self.sp.current_user_playlists, offset=offset
            )
            playlists.extend(
                playlist
                for playlist in playlist_batch.get("items", [])
                if playlist.get("owner", {}).get("id") == self.user_id
            )
            if playlist_batch.get("next"):
                offset += 50
            else:
                break
        return playlists

    def send_request(self, request, **kwargs):
        delta_time = time.time() - self.recent_request
        if delta_time < 1:
            time.sleep(1 - delta_time)
        try:
            request_output = request(**kwargs)
            self.recent_request = time.time()
            return request_output
        except spotipy.exceptions.SpotifyException as e:
            print(e)
            return None


class File:
    def __init__(self, file_path: str) -> None:
        self.path: str = file_path
        self.name: str = os.path.basename(file_path)

    def get_bytes(self, compressed: bool = True) -> list[int]:
        with open(self.path, "rb") as f:
            if compressed:
                compressed_data = list(gz.compress(f.read()))
                return compressed_data
            else:
                return list(f.read())


def sha256_encrypt(data):
    data_str = str(data)
    return hashlib.sha256(data_str.encode()).hexdigest()


def upload_to_spotify(
        file_path: str | None = None,
        is_compressed: bool = True,
        track_id_database: str = "13bit_ids.db",
        max_playlist_size: int = 10_001 - 13,
        bits_per_track: int = 13,
        is_print_progress: bool = True,
        is_confirmation_prompt: bool = True,
) -> str:
    file: File = File(file_path or open_file_dialog(dialog_type="file"))
    file_bytes: list[int] = file.get_bytes(compressed=is_compressed)

    track_count: int = (8 * len(file_bytes)) // bits_per_track + (
            8 * len(file_bytes)
    ) % bits_per_track
    playlist_count: int = ceil(track_count / max_playlist_size)
    if is_confirmation_prompt:
        print(
            f"{file.path}\n",
            f"{len(file_bytes)} bytes\n",
            f"{track_count} tracks\n",
            f"{playlist_count} playlists\n",
            f"Time estimate: {ceil(track_count / 85)}s",
        )
        input("Press enter to continue. Press ctrl + c to quit.")

    playlist_ids = add_bytes_to_spotify(
        bytes_to_add=file_bytes,
        bits_per_track=bits_per_track,
        max_playlist_size=max_playlist_size,
        track_id_database=track_id_database,
        print_progress=is_print_progress,
    )

    header_string = "*".join([file.name] + playlist_ids)
    header_bytes = list(header_string.encode("utf-8"))
    header_playlist_id = add_bytes_to_spotify(
        bytes_to_add=header_bytes,
        bits_per_track=bits_per_track,
        max_playlist_size=max_playlist_size,
        track_id_database=track_id_database,
        name=f"{file.path} Header",
        print_progress=False,
    )

    return header_playlist_id[0]


def add_bytes_to_spotify(
        bytes_to_add: list[int],
        bits_per_track: int,
        max_playlist_size: int,
        track_id_database: str,
        name: str = str(time.time()),
        print_progress: bool = True,
) -> list[str]:
    binary = binary_bytes_conversion(bytes_to_add, conversion_type="bytes_to_binary")
    track_ids: list[str] = []
    with sqlite3.connect(track_id_database) as db_connection:
        db_cursor: Cursor = db_connection.cursor()
        for chunk in batch(binary, bits_per_track):
            if len(chunk) == bits_per_track:
                track_ids.append(
                    db_query(
                        output_column="track_id",
                        reference_column="binary",
                        query=str(chunk),
                        table="_13bit_ids",
                        cursor=db_cursor,
                    )
                )
            else:
                for byte in chunk:
                    track_ids.append(
                        db_query(
                            output_column="track_id",
                            reference_column="binary",
                            query=str(byte),
                            table="_13bit_ids",
                            cursor=db_cursor,
                        )
                    )
        db_cursor.close()

    playlist_ids: list[str] = []
    for chunk in batch(track_ids, max_playlist_size):
        playlist_ids.append(
            api_request_manager.send_request(
                request=api_request_manager.sp.user_playlist_create,
                user=api_request_manager.user_id,
                name=sha256_encrypt(name),
            )["id"]
        )
        api_request_manager.add_tracks_to_playlist(
            playlist_ids[-1], chunk, print_progress=print_progress
        )

    return playlist_ids


def get_bytes_from_spotify(
        playlist_ids: list[str],
        database: str = "13bit_ids.db",
        is_print_progress: bool = True,
) -> list[int]:
    binary: list[int] = []
    with sqlite3.connect(database) as db_connection:
        db_cursor: Cursor = db_connection.cursor()
        for playlist_id in playlist_ids:
            playlist_tracks = api_request_manager.get_playlist_tracks(
                playlist_id, is_print_progress
            )
            for track in playlist_tracks:
                track_binary_str: str = db_query(
                    output_column="binary",
                    reference_column="track_identifier",
                    query=f"{track['name']}{[artist['name'] for artist in track['artists']]}{track['album']['name']}",
                    table="_13bit_ids",
                    cursor=db_cursor,
                )
                track_binary: list[int] | int = eval(track_binary_str)
                if type(track_binary) is list:
                    binary.extend(track_binary)
                else:
                    binary.append(track_binary)

    return binary_bytes_conversion(binary, "binary_to_bytes")


def download_from_spotify(
        header_playlist_id: str,
        file_destination: str,
        track_id_database: str = "13bit_ids.db",
        is_confirm_read: bool = True,
        is_print_progress: bool = True,
) -> None:
    header_bytes = get_bytes_from_spotify(
        playlist_ids=[header_playlist_id],
        database=track_id_database,
        is_print_progress=False,
    )
    header_string = bytes(header_bytes).decode("utf-8")
    playlist_ids = header_string.split("*")
    filename = playlist_ids.pop(0)

    file_bytes: list[int] = get_bytes_from_spotify(
        playlist_ids=playlist_ids,
        database=track_id_database,
        is_print_progress=is_print_progress,
    )

    with open(f"{file_destination}\\{filename}", "wb") as f:
        f.write(gz.decompress(bytes(file_bytes)))

    return None


def remove_from_spotify(header_playlist_id: str) -> None:
    header_playlist_id = api_request_manager.send_request(
        request=api_request_manager.sp.playlist, playlist_id=header_playlist_id
    )["id"]
    header_bytes = get_bytes_from_spotify(
        playlist_ids=[header_playlist_id], is_print_progress=False
    )
    header_string = bytes(header_bytes).decode("utf-8")
    playlist_ids = header_string.split("*")
    playlist_ids.pop(0)
    playlist_ids.append(header_playlist_id)

    for playlist_id in playlist_ids:
        api_request_manager.send_request(
            request=api_request_manager.sp.current_user_unfollow_playlist,
            playlist_id=playlist_id,
        )


class FileEnvironment:
    def __init__(self, environment_playlist_id: str) -> None:
        environment_bytes: list[int] = get_bytes_from_spotify(
            [environment_playlist_id], is_print_progress=False
        )
        self.file_system: dict = pickle.loads(bytes(environment_bytes))
        self.current_path = ["main"]
        self.current_directory = CurrentEnvironmentDirectory(
            self.file_system, self.current_path
        )

    def update_playlist(self) -> None:
        pass


class CurrentEnvironmentDirectory:
    def __init__(self, file_system: dict, current_path: list[str]):
        self.parent_directory: list = current_path[:-1]
        self.current_directory: dict = file_system

        assert current_path[0] == "main"

        for folder in current_path:
            self.current_directory = self.current_directory[folder]

    @property
    def files(self) -> list[str]:
        files: list[str] = []
        for _, val in self.current_directory.items():
            if type(val) is str:
                files.append(val)
        return files

    @property
    def folders(self) -> list[str]:
        folders: list[str] = []
        for key, val in self.current_directory.items():
            if type(val) is dict:
                folders.append(key)
        return folders

    def __str__(self) -> str:
        folders_list: list = ["Folders:"] + self.folders
        files_list: list = ["Files:"] + self.files
        return "\n".join(folders_list + files_list)


api_request_manager: APIRequests = APIRequests()

if __name__ == "__main__":
    # upload_to_spotify()
    # download_from_spotify(
    #     input("Header\n"), file_destination=open_file_dialog("directory")
    # )
    # upload_to_spotify()
    # remove_from_spotify(input("H id?\n"))
    pass
