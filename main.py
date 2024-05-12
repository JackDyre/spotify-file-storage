import gzip as gz
import hashlib
import json
import os
import sqlite3
import sys
import time
import tkinter as tk
from math import ceil
from sqlite3 import Connection, Cursor
from tkinter import filedialog
from typing import Generator, Iterable

import pyperclip  # type: ignore
import spotipy  # type: ignore
from spotipy.oauth2 import SpotifyClientCredentials  # type: ignore
from spotipy.oauth2 import SpotifyOAuth


def print_progress_bar(iteration, total, prefix="", suffix="", length=50, fill="X"):
    percent = ("{0:.1f}").format(100 * ((iteration + 1) / float(total)))
    filled_length = int(length * (iteration + 1) // total)
    bar = fill * filled_length + "-" * (length - filled_length)
    print(f"\r{prefix} |{bar}| {percent}% {suffix}", end="")
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
    if dialog_type =="file":
        return filedialog.askopenfilename()
    raise ValueError("Invalid filedialog type")


def binary_bytes_conversion(binary: Iterable | list[int], conversion_type: str = "binary_to_bytes") -> list[int]:
    if conversion_type == "binary_to_bytes":
        return list(bytearray(int(''.join(map(str, byte)), 2) for byte in batch(binary, 8)))
    elif conversion_type == "bytes_to_binary":
        return [int(bit) for byte in bytearray(binary) for bit in bin(byte)[2:].zfill(8)]
    raise ValueError("Invalid conversion type. Valid types are: 'binary_to_bytes' and 'bytes_to_binary'")


class APIRequests:
    def __init__(self) -> None:
        self.recent_request: float = time.time()
        self.sp: spotipy.Spotify = self.create_client()
        self.user_id: str = self.send_request(request=self.sp.current_user)["id"]

    def create_client(self) -> spotipy.Spotify:
        try:
            with open("api-credentials.json", "r") as f:
                api_dict = json.load(f)
            client_id = api_dict["cl-id"]
            client_secret = api_dict["cl-secr"]
        except FileNotFoundError:
            client_id = input("Client ID?\n")
            client_secret = input("Client Secret?\n")
            with open("api-credentials.json", "w") as f:
                json.dump({"cl-id": client_id, "cl-secr": client_secret}, f)

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

    def get_playlist_tracks(self, playlist: str) -> list[dict]:
        offset: int = 0
        tracks: list[dict] = []
        while True:
            track_batch = self.send_request(
                request=self.sp.user_playlist_tracks,
                user=self.user_id,
                playlist_id=playlist,
                offset=offset,
                market="US",
            )
            offset += 100

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
                request=self.sp.user_playlist_add_tracks,
                playlist_id=playlist,
                user = self.user_id,
                tracks=track_batch,
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


# -------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------


class File:
    def __init__(self, file_path: str) -> None:
        self.path: str = file_path
        self.name: str = os.path.basename(file_path)

    def get_binary(self, compressed: bool = True) -> list[int]:
        with open(self.path, "rb") as f:
            if compressed:
                compressed_data = list(gz.compress(f.read()))
                return binary_bytes_conversion(list(compressed_data), "bytes_to_binary")
            else:
                return binary_bytes_conversion(list(f.read()), "bytes_to_binary")


def get_file_binary(file: File, is_compressed: bool = True) -> list[int]:
    if is_compressed:
        return file.get_binary(compressed=True)
    else:
        return file.get_binary(compressed=False)


def write_confirmation_prompt(track_count, playlist_count) -> bool:
    print(f"\nTracks needed: {track_count}")
    print(f"Playlists needed: {playlist_count}")
    print(f"Time estimate: {ceil(track_count / 100)}s")
    confirmation = input("Confirm? (Y/N)\n")
    print("\n")
    if confirmation.upper() == "Y":
        return True
    return False


def split_binary_into_tracks(
    binary: list, bits_per_track: int, database: str
) -> Generator:
    
    with sqlite3.connect(database) as db_connection:

        db_cursor: Cursor = db_connection.cursor()

        for track_data in batch(binary, bits_per_track):
            if len(track_data) == bits_per_track:
                yield lookup_id_in_db(track_data, db_cursor)
            else:
                for byte in track_data:
                    yield lookup_id_in_db(byte, db_cursor)

        db_cursor.close()


def lookup_id_in_db(binary: list, cursor: Cursor) -> str:
    cursor.execute("SELECT * FROM _13bit_ids WHERE binary = ?", (str(binary),))
    track_id = cursor.fetchall()[0][1]
    return track_id


def upload_to_spotify(
    is_compressed: bool = True,
    lookup_db: str = "13bit_ids.db",
    max_tracks_per_playlist: int = 9_985,
    bits_per_track: int = 13,
    print_progress: bool = True,
    confirm_write: bool = True,
) -> str | None:

    file = File(open_file_dialog(dialog_type="file"))

    file_binary: list[int] = get_file_binary(file=file, is_compressed=is_compressed)

    track_count = len(file_binary) // 13 + len(file_binary) % 13
    playlist_count = ceil(track_count / max_tracks_per_playlist)

    if confirm_write and not write_confirmation_prompt(track_count, playlist_count):
        return None

    playlist_ids: list[str] = []
    for idx, playlist_batch in enumerate(
        batch(
            split_binary_into_tracks(file_binary, bits_per_track, lookup_db),
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

        if print_progress:
            print(
                f"Dumping {len(list(playlist_batch))} tracks into playlist {idx} of {playlist_count}"
            )
        api_request_manager.add_tracks_to_playlist(
            playlist=playlist_id,
            tracks=list(playlist_batch),
            print_progress=print_progress,
        )

    header_string = "*".join([file.name] + playlist_ids)
    header_tracks = split_binary_into_tracks(
        binary_bytes_conversion(list(header_string.encode("utf-8")), "bytes_to_binary"),
        bits_per_track,
        lookup_db,
    )

    header_id = api_request_manager.send_request(
        api_request_manager.sp.user_playlist_create,
        user=api_request_manager.user_id,
        name=f"{file.name}: Header Playlist",
    )["id"]

    api_request_manager.add_tracks_to_playlist(
        playlist=header_id, tracks=list(header_tracks)
    )

    pyperclip.copy(header_id)
    if print_progress:
        print("\nHeader playlist ID copied to clipboard")

    return header_id


# -------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------


def read_binary_from_playlist(playlist: str, database: str) -> Generator:
    db_connection: Connection = sqlite3.connect(database)
    db_cursor: Cursor = db_connection.cursor()

    tracks: list[dict] = api_request_manager.get_playlist_tracks(playlist)
    for track in tracks:
        db_cursor.execute(
            "SELECT * FROM _13bit_ids WHERE track_identifier = ?",
            (
                f"{track['name']}{[artist['name'] for artist in track['artists']]}{track['album']['name']}",
            ),
        )
        binary: list[int] | int = eval(db_cursor.fetchall()[0][0])
        if type(binary) is int:
            binary = [binary]
        for bit in binary:  # type: ignore
            yield bit

    db_cursor.close()
    db_connection.close()



def read_confirmation_prompt(playlist_ids: list[str]) -> bool:
    total_tracks: int = 0
    for playlist in playlist_ids:
        total_tracks += api_request_manager.send_request(
            request=api_request_manager.sp.playlist, playlist_id=playlist
        )["tracks"]["total"]

    print(f"Total tracks: {total_tracks}")
    print(f"Time estimate: {ceil(total_tracks / 100)}s")
    confirmation = input("Confirm (Y/N)\n")
    if confirmation.upper() == "Y":
        return True
    return False


def read_from_playlist(
    header_playlist: str,
    destination: str,
    lookup_db: str = "13bit_ids.db",
    confirm_read: bool = False,
    print_progress: bool = False,
) -> str | None:

    header_string: str = bytes(
        binary_bytes_conversion(read_binary_from_playlist(header_playlist, lookup_db), "binary_to_bytes")
    ).decode("utf-8")

    playlist_ids: list[str] = header_string.split("*")
    filename = playlist_ids.pop(0)

    if confirm_read and not read_confirmation_prompt(playlist_ids):
        return None

    file_binary: list[int] = []
    for playlist in playlist_ids:
        playlist_binary = read_binary_from_playlist(playlist, lookup_db)
        file_binary.extend(playlist_binary)
    file_bytes = binary_bytes_conversion(file_binary, "binary_to_bytes")

    with open(f"{filename}.gz", "wb") as f:
        f.write(bytes(file_bytes))

    with open(f"{destination}\\{filename}", "wb") as uncompressed_file:
        with gz.open(f"{filename}.gz", "rb") as compressed_file:
            uncompressed_file.write(compressed_file.read())

    os.remove(f"{filename}.gz")

    return f"{destination}/{filename}"




# -------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------


# class FileEnvironment:
#     def __init__(self, id: str) -> None:
#         self.contents: dict[str, str | dict] = {}
#         self.id: str = id

#     def update(self):
#         old_tracks = api_request_manager.get_playlist_tracks(playlist=self.id)
#         for track in old_tracks:
#             api_request_manager.send_request(
#                 api_request_manager.sp.playlist_remove_all_occurrences_of_items,
#                 playlist_id=self.id,
#                 items=[track["id"]],
#             )
#         new_tracks = split_binary_into_tracks(
#             bytes_to_binary(str(self.contents).encode("utf-8")), 13, "13bit_ids.db"
#         )
#         api_request_manager.add_tracks_to_playlist(
#             playlist=self.id, tracks=list(new_tracks)
#         )


# def sha256_encrypt(data):
#     data_str = str(data)
#     return hashlib.sha256(data_str.encode()).hexdigest()


# def file_envirnment_search() -> FileEnvironment:
#     environment_name = input("Environment name?\n")
#     environment_password = input("Environment password?\n")
#     environment_passkey = "".join([environment_name, environment_password])

#     user_playlists = api_request_manager.get_user_playlists()
#     for playlist in user_playlists:
#         if playlist["name"] == sha256_encrypt(
#             "spotify-file-storage-environment"
#         ) and playlist["description"] == sha256_encrypt(environment_passkey):
#             env = FileEnvironment(playlist["id"])
#             z = read_binary_from_playlist(playlist["id"], "13bit_ids.db")
#             y = bytes(z)
#             x = y.decode("utf-8")
#             print(x)
#             env.contents = eval(x)
#             return env
#     print("No file environment found\n\nCreating new file environment...")
#     env_id = api_request_manager.send_request(
#         api_request_manager.sp.user_playlist_create,
#         user=api_request_manager.user_id,
#         name=sha256_encrypt("spotify-file-storage-environment"),
#         description=sha256_encrypt(environment_passkey),
#     )["id"]
#     env = FileEnvironment(env_id)
#     env.update()
#     return env


api_request_manager: APIRequests = APIRequests()

if __name__ == "__main__":
    upload_to_spotify()
