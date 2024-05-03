import os
import sys
import time
from math import ceil
import sqlite3

import spotipy  # type: ignore
from spotipy.oauth2 import SpotifyClientCredentials, SpotifyOAuth  # type: ignore


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
    fill = "█"

    percent = ("{0:.1f}").format(100 * (iteration / float(total)))
    filled_length = int(length * iteration // total)
    bar = fill * filled_length + "-" * (length - filled_length)
    sys.stdout.write("\r%s |%s| %s%% %s" % (prefix, bar, percent, suffix)),
    sys.stdout.flush()
    if iteration == total:
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


def create_client() -> spotipy.Spotify:

    try:
        with open("api-credentials.txt", "r") as f:
            api_dict = eval(f.read())
        client_id = api_dict["cl-id"]
        client_secret = api_dict["cl-secr"]
    except:
        client_id = input("Client ID?\n")
        client_secret = input("Client Secret?\n")

    with open("api-credentials.txt", "w") as f:
        f.write(str({"cl-id": client_id, "cl-secr": client_secret}))

    try:
        spotipy.Spotify(
            auth_manager=SpotifyClientCredentials(
                client_id=client_id, client_secret=client_secret
            )
        )
    except:
        os.remove("api-credentials.txt")
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


def batch(iterable, batch_size):
    for i in range(0, len(iterable), batch_size):
        yield iterable[i : i + batch_size]


class APIRequests:
    def __init__(self) -> None:
        self.recent_request: float = time.time()
        self.sp: spotipy.Spotify = create_client()
        self.user_id: str = self.sp.current_user()["id"]

    def get_playlist_tracks(self, playlist: str, offset: int, retries: int = 0):
        return self.send_request(
            request=self.sp.user_playlist_tracks,
            user=self.user_id,
            playlist_id=playlist,
            offset=offset,
            market="US",
        )

    def add_tracks_to_playlist(self, playlist: str, tracks: list):
        return self.send_request(
            request=self.sp.user_playlist_add_tracks,
            user=self.user_id,
            playlist_id=playlist,
            tracks=tracks,
        )

    def create_playlist(self, name: str):
        return self.send_request(
            request=self.sp.user_playlist_create, user=self.user_id, name=name
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


def get_playlist_tracks(playlist: str) -> list:
    offset: int = 0
    tracks: list = []
    while True:
        track_batch = api_request_manager.get_playlist_tracks(playlist, offset)
        offset += 100
        for track in track_batch["items"]:
            tracks.append(track["track"])
        if not track_batch["next"]:
            break

    return tracks


def add_tracks_to_playlist(playlist, tracks):
    for track_batch in batch(tracks, 100):
        api_request_manager.add_tracks_to_playlist(playlist, track_batch)


def create_playlist(name):
    playlist = api_request_manager.create_playlist(name)
    return playlist


def create_ref_playlist():
    with open("8194-ids.txt", "r") as f:
        ref_ids = eval(f.read())

    ref_playlist = create_playlist("reference bit dictionary")

    add_tracks_to_playlist(ref_playlist["id"], ref_ids)

    return ref_playlist


def encode_file(file, ref_ids_input=None) -> str | None:
    with open("8194-ids.txt", "r") as f:
        ref_ids = ref_ids_input or eval(f.read())

    filename = os.path.basename(file)
    with open(file, "rb") as f:  # type: ignore
        file_bytes = list(f.read())

    file_binary: list = []
    for idx, byte in enumerate(file_bytes):
        print_progress_bar(idx, len(file_bytes))
        file_binary.extend(decimal_to_binary_padded(byte, 8))

    conn = sqlite3.connect("pad_13_lookup.db")
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
        playlist_id = create_playlist(
            f"{filename}: Playlist {playlist_iter} of {playlist_count}"
        )["id"]
        playlist_ids.append(playlist_id)

        for track_data in batch(playlist_data, 13):
            if len(track_data) == 13:
                cursor.execute(
                    "SELECT * FROM pad13_id_lookup WHERE binary = ?", (str(track_data),)
                )
                track_id = cursor.fetchall()
                track_ids.append(track_id[0][1])
            else:
                for byte in track_data:
                    cursor.execute(
                        "SELECT * FROM pad13_id_lookup WHERE binary = ?", (str(byte),)
                    )
                    track_id = cursor.fetchall()
                    track_ids.append(track_id[0][1])

        print(f"Dumping tracks to playlist {playlist_iter} of {playlist_count}...")
        print(f"Playlist size: {len(track_ids)}\n")
        add_tracks_to_playlist(playlist_id, track_ids)

    header_playlist = create_playlist(f"{filename}: Header Playlist")["id"]
    header_string = "*".join([filename] + playlist_ids)
    header_bytes = list(header_string.encode("utf-8"))

    header_binary = []
    for idx, byte in enumerate(header_bytes):
        header_binary.extend(decimal_to_binary_padded(byte, 8))

    header_track_ids: list = []
    for header_track_data in batch(header_binary, 13):
        if len(header_track_data) == 13:
            cursor.execute(
                "SELECT * FROM pad13_id_lookup WHERE binary = ?",
                (str(header_track_data),),
            )
            track_id = cursor.fetchall()
            header_track_ids.append(track_id[0][1])
        else:
            for byte in header_track_data:
                cursor.execute(
                    "SELECT * FROM pad13_id_lookup WHERE binary = ?", (str(byte),)
                )
                track_id = cursor.fetchall()
                header_track_ids.append(track_id[0][1])

    print(f"Dumping tracks to header playlist...")
    print(f"Header size: {len(header_track_ids)}")
    add_tracks_to_playlist(header_playlist, header_track_ids)

    cursor.close()
    conn.close()
    return header_playlist


def decode_file(header_playlist_id, destination, ref_ids_input=None):
    header_tracks = get_playlist_tracks(header_playlist_id)

    with open("8194-ids.txt", "r") as f:
        ref_ids = ref_ids_input or eval(f.read())

    decode_dict = {}
    for idx, id in enumerate(ref_ids[:8192]):
        decode_dict[id] = decimal_to_binary_padded(idx, 13)
    for idx, id in enumerate(ref_ids[-2:]):
        decode_dict[id] = [idx]

    header_binary = []
    for track in header_tracks:
        header_binary.extend(decode_dict[track["id"]])

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
        tracks = get_playlist_tracks(playlist)
        total_tracks.extend(tracks)

    print("Reconstructing file...")
    file_binary = []
    for track in total_tracks:
        file_binary.extend(decode_dict[track["id"]])

    file_bytes = []
    for byte in batch(file_binary, 8):
        file_bytes.append(sum(bit * (2 ** (7 - idx)) for idx, bit in enumerate(byte)))

    with open(f"{destination}\\{filename}", "wb") as f:
        f.write(bytes(file_bytes))

    return filename


if __name__ == "__main__":
    pass
