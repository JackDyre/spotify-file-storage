import json
import os
import sqlite3
import sys
import time
from math import ceil

import spotipy  # type: ignore
from spotipy.oauth2 import SpotifyClientCredentials  # type: ignore
from spotipy.oauth2 import SpotifyOAuth


def print_progress_bar(iteration, total):
    """
    Call in a loop to create terminal progress bar.
    :param iteration: current iteration (Int)
    :param total: total iterations (Int)
    :param prefix: prefix string (Str)
    :param suffix: suffix string (Str)
    :param length: character length of bar (Int)
    :param fill: bar fill character (Str)
    :return: None
    """
    prefix = ""
    suffix = ""
    length = 50
    fill = "X"

    percent = ("{0:.1f}").format(100 * ((iteration + 1) / float(total)))
    filled_length = int(length * (iteration + 1) // total)
    bar = fill * filled_length + "-" * (length - filled_length)
    sys.stdout.write("\r%s |%s| %s%% %s" % (prefix, bar, percent, suffix)),
    sys.stdout.flush()
    if iteration + 1 == total:
        sys.stdout.write("\n")
        sys.stdout.flush()


def decimal_to_binary_padded(decimal, pad):
    binary = ""
    while decimal > 0:
        remainder = decimal % 2
        binary = str(remainder) + binary
        decimal = decimal // 2
    binary = binary.zfill(pad)
    return [int(bit) for bit in binary]


def batch(iterable, batch_size):
    for i in range(0, len(iterable), batch_size):
        yield iterable[i : i + batch_size]


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
        except:
            client_id = input("Client ID?\n")
            client_secret = input("Client Secret?\n")

        with open("api-credentials.json", "w") as f:
            json.dump({"cl-id": client_id, "cl-secr": client_secret}, f)

        try:
            spotipy.Spotify(
                auth_manager=SpotifyClientCredentials(
                    client_id=client_id, client_secret=client_secret
                )
            )
        except:
            os.remove("api-credentials.json")
            print("\n\nInvalid API info")
            sys.exit()

        sp: spotipy.Spotify = spotipy.Spotify(
            retries=0,
            auth_manager=SpotifyOAuth(
                client_id=client_id,
                client_secret=client_secret,
                scope="playlist-read-private playlist-modify-public playlist-modify-private",
                redirect_uri="http://localhost:8888/callback",
            ),
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

    def add_tracks_to_playlist(self, playlist: str, tracks: list) -> None:
        for track_batch in batch(tracks, 100):
            self.send_request(
                request=self.sp.user_playlist_add_tracks,
                user=self.user_id,
                playlist_id=playlist,
                tracks=track_batch,
            )

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


api_request_manager: APIRequests = APIRequests()


def encode_file(file, ref_ids_input=None) -> str | None:
    filename = os.path.basename(file)
    with open(file, "rb") as f:  # type: ignore
        file_bytes = list(f.read())

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


def decode_file(header_playlist_id, destination, ref_ids_input=None):

    conn = sqlite3.connect("13bit_ids.db")
    cursor = conn.cursor()

    header_tracks = api_request_manager.get_playlist_tracks(header_playlist_id)

    header_binary = []
    for track in header_tracks:
        cursor.execute(
            "SELECT * FROM _13bit_ids WHERE track_identifier = ?", (f"{track['name']}{[artist['name'] for artist in track['artists']]}",)
        )
        binary = eval(cursor.fetchall()[0][0])
        if type(binary) is int:
            binary = [binary]
        header_binary.extend(binary)

    header_bytes = []
    for byte in batch(header_binary, 8):
        header_bytes.append(sum(bit * (2 ** (7 - idx)) for idx, bit in enumerate(byte)))

    header_string = bytes(header_bytes).decode("utf-8")
    playlist_ids = header_string.split("*")
    filename = playlist_ids.pop(0)

    total_tracks = []
    playlist_iter = 0
    for playlist in playlist_ids:
        playlist_iter += 1
        print(
            f"Fetching tracks from playlist {playlist_iter} of {len(playlist_ids)}..."
        )
        tracks = api_request_manager.get_playlist_tracks(playlist)
        total_tracks.extend(tracks)

    file_binary = []
    for track in total_tracks:
        cursor.execute(
            "SELECT * FROM _13bit_ids WHERE track_identifier = ?", (f"{track['name']}{[artist['name'] for artist in track['artists']]}",)
        )
        binary = eval(cursor.fetchall()[0][0])
        if type(binary) is int:
            binary = [binary]
        file_binary.extend(binary)

    print("Reconstructing file...")
    file_bytes = []
    for byte in batch(file_binary, 8):
        file_bytes.append(sum(bit * (2 ** (7 - idx)) for idx, bit in enumerate(byte)))

    with open(f"{destination}\\{filename}", "wb") as f:
        f.write(bytes(file_bytes))

    cursor.close()
    conn.close()
    return filename
