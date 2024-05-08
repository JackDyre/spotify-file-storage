import json
import os
import sys
import time

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