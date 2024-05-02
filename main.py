import os
import sys
import time
from math import ceil

import spotipy  # type: ignore
from spotipy.oauth2 import SpotifyOAuth  # type: ignore
from spotipy.oauth2 import SpotifyClientCredentials # type: ignore



def print_progress_bar(iteration, total, prefix="", suffix="", length=50, fill="█"):
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
        with open('api-credentials.txt', 'r') as f:
            api_dict = eval(f.read())
        client_id = api_dict['cl-id']
        client_secret = api_dict['cl-secr']
    except:
        client_id = input('Client ID?\n')
        client_secret = input('Client Secret?\n')

    with open('api-credentials.txt', 'w') as f:
            f.write(str({'cl-id': client_id, 'cl-secr': client_secret}))

    try:
        spotipy.Spotify(
            auth_manager=SpotifyClientCredentials(
                client_id=client_id,
                client_secret=client_secret
                )
            )
    except:
        os.remove('api-credentials.txt')
        print('\n\nInvalid API info')
        sys.exit()


    sp: spotipy.Spotify = spotipy.Spotify(
        retries=0,
        auth_manager=SpotifyOAuth(
            client_id=client_id,
            client_secret=client_secret,
            scope='playlist-read-private playlist-modify-public playlist-modify-private',
            redirect_uri='http://localhost:8888/callback'
        )
    )
    return sp

def batch(iterable, batch_size):
    for i in range(0, len(iterable), batch_size):
        yield iterable[i : i + batch_size]

class APIRequests:
    def __init__(self) -> None:
        self.recent_request: float = time.time()
        self.sp: spotipy.Spotify = create_client()
        self.user_id: str = self.sp.current_user()['id']

    def get_playlist_tracks(self, playlist: str, offset: int, retries: int=0):
        delta_time = time.time() - self.recent_request
        if delta_time > .5:
            try:
                self.recent_request = time.time()
                return self.sp.user_playlist_tracks(self.user_id, playlist, offset=offset, market='US')
            except spotipy.exceptions.SpotifyException as e:
                if e.http_status == 429:
                    print(e)
                    print(e.headers.get('Retry-After'))
                    print(f'retrying: waiting {(2 ** retries) * 4} seconds...')
                    time.sleep((2 ** retries) * 4)
                    retries += 1
                    return self.get_playlist_tracks(playlist, offset, retries)
                else:
                    raise e
        else:
            time.sleep(.5 - delta_time)
            return self.get_playlist_tracks(playlist, offset, 0)
    
    def add_tracks_to_playlist(self, playlist: str, tracks: list, retries: int=0):
        delta_time = time.time() - self.recent_request
        if delta_time > .5:
            try:
                self.recent_request = time.time()
                return self.sp.user_playlist_add_tracks(user=self.user_id, playlist_id=playlist, tracks=tracks)
            except spotipy.exceptions.SpotifyException as e:
                if e.http_status == 429:
                    print(e)
                    print(e.headers.get('Retry-After'))
                    print(f'retrying: waiting {(2 ** retries) * 4} seconds...')
                    time.sleep((2 ** retries) * 4)
                    retries += 1
                    return self.add_tracks_to_playlist(playlist, tracks, retries)
                else:
                    raise e
        else:
            time.sleep(.5 - delta_time)
            return self.add_tracks_to_playlist(playlist, tracks, 0)
    
    def create_playlist(self, name: str, retries: int=0):
        delta_time = time.time() - self.recent_request
        if delta_time > .5:
            try:
                self.recent_request = time.time()
                return self.sp.user_playlist_create(self.user_id, name)
            except spotipy.exceptions.SpotifyException as e:
                if e.http_status == 429:
                    print(e)
                    print(e.headers.get('Retry-After'))
                    print(f'retrying: waiting {(2 ** retries) * 4} seconds...')
                    time.sleep((2 ** retries) * 4)
                    retries += 1
                    return self.create_playlist(name, retries)
                else:
                    raise e
        else:
            time.sleep(.5 - delta_time)
            return self.create_playlist(name, 0)

api_client: APIRequests = APIRequests()

def get_playlist_tracks(playlist: str) -> list:
    offset: int = 0
    tracks: list = []
    while True:
        track_batch = api_client.get_playlist_tracks(playlist, offset)
        offset += 100
        for track in track_batch['items']:
            tracks.append(track['track'])
        if not track_batch["next"]:
                break
    
    return tracks

def add_tracks_to_playlist(playlist, tracks):
    for track_batch in batch(tracks, 100):
        api_client.add_tracks_to_playlist(playlist, track_batch)

def create_playlist(name):
    playlist = api_client.create_playlist(name)
    return playlist
    
def create_ref_playlist():
    with open('8194-ids.txt', 'r') as f:
        ref_ids = eval(f.read())
    
    ref_playlist = create_playlist('reference bit dictionary')

    add_tracks_to_playlist(ref_playlist['id'], ref_ids)

    return ref_playlist

def encode_file(file, ref_ids_input = None) -> str:
    with open('8194-ids.txt', 'r') as f:
        ref_ids = ref_ids_input or eval(f.read())


    filename = os.path.basename(file)
    with open(file, "rb") as f: # type: ignore
        file_bytes = list(f.read())
        
    file_binary: list = []
    for idx, byte in enumerate(file_bytes):
        print_progress_bar(idx, len(file_bytes))
        file_binary.extend(decimal_to_binary_padded(byte, 8))
    
    encode_dict = {}
    for idx, id in enumerate(ref_ids[:8192]):
        encode_dict[str(decimal_to_binary_padded(idx, 13))] = id
    for idx, id in enumerate(ref_ids[-2:]):
        encode_dict[str(idx)] = id
    
    song_count = (len(file_binary) // 13) + (len(file_binary) % 13)
    playlist_count = ceil(song_count / 9_975)

    print(f'\n\nDumping {song_count} tracks into {playlist_count} playlists...\n\n')


    playlist_ids: list = []
    playlist_iter = 0
    for playlist_data in batch(file_binary, 9_975 * 13):

        track_ids: list = []

        playlist_iter += 1
        playlist_id = create_playlist(f'{filename}: Playlist {playlist_iter} of {playlist_count}')['id']
        playlist_ids.append(playlist_id)

        for track_data in batch(playlist_data, 13):
            if len(track_data) == 13:
                track_ids.append(encode_dict[str(track_data)])
            else:
                for byte in track_data:
                    track_ids.append(encode_dict[str(byte)])

        print(f'Dumping tracks to playlist {playlist_iter} of {playlist_count}...')
        print(f'Playlist size: {len(track_ids)}\n')
        add_tracks_to_playlist(playlist_id, track_ids)

    header_playlist = create_playlist(f'{filename}: Header Playlist')['id']
    header_string = '*'.join([filename] + playlist_ids)
    header_bytes = list(header_string.encode('utf-8'))

    header_binary = []
    for idx, byte in enumerate(header_bytes):
        header_binary.extend(decimal_to_binary_padded(byte, 8))

    header_track_ids: list = []
    for header_track_data in batch(header_binary, 13):
        if len(header_track_data) == 13:
            header_track_ids.append(encode_dict[str(header_track_data)])
        else:
            for byte in header_track_data:
                header_track_ids.append(encode_dict[str(byte)])
    
    print(f'Dumping tracks to header playlist...')
    print(f'Header size: {len(header_track_ids)}')
    add_tracks_to_playlist(header_playlist, header_track_ids)

    return header_playlist
        
def decode_file(header_playlist_id, ref_ids_input = None):
    header_tracks = get_playlist_tracks(header_playlist_id)

    with open('8194-ids.txt', 'r') as f:
        ref_ids = ref_ids_input or eval(f.read())

    decode_dict = {}
    for idx, id in enumerate(ref_ids[:8192]):
        decode_dict[id] = decimal_to_binary_padded(idx, 13)
    for idx, id in enumerate(ref_ids[-2:]):
        decode_dict[id] = [idx]

    
    header_binary = []
    for track in header_tracks:
        header_binary.extend(decode_dict[track['id']])
    
    header_bytes = []
    for byte in batch(header_binary, 8):
        header_bytes.append(sum(bit * (2 ** (7 - idx)) for idx, bit in enumerate(byte)))
    
    header_string = bytes(header_bytes).decode('utf-8')
    playlist_ids = header_string.split('*')
    filename = playlist_ids.pop(0)


    total_tracks = []
    for playlist in playlist_ids:
        tracks = get_playlist_tracks(playlist)
        total_tracks.extend(tracks)
    
    file_binary = []
    for track in total_tracks:
        file_binary.extend(decode_dict[track['id']])
    
    file_bytes = []
    for byte in batch(file_binary, 8):
        file_bytes.append(sum(bit * (2 ** (7 - idx)) for idx, bit in enumerate(byte)))

    with open(filename, 'wb') as f:
        f.write(bytes(file_bytes))
    
    return filename


