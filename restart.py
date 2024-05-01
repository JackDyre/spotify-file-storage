import spotipy # type: ignore
from spotipy.oauth2 import SpotifyOAuth # type: ignore
import time

def create_client() -> spotipy.Spotify:
    sp: spotipy.Spotify = spotipy.Spotify(
        retries=0,
        auth_manager=SpotifyOAuth(
            client_id='592557b25f744f2abdd7234c2d668346',
            client_secret='86e134b4e36e4e71b5952c6dc586dd44',
            scope='playlist-read-private playlist-modify-public playlist-modify-private',
            redirect_uri='http://localhost:8888/callback'
        )
    )
    return sp

def batch(iterable, batch_size):
    for i in range(0, len(iterable), batch_size):
        yield iterable[i : i + batch_size]

class APIRequests:
    def __init__(self, user_id: str) -> None:
        self.recent_request: float = time.time()
        self.sp: spotipy.Spotify = create_client()
        self.user_id: str = user_id

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

api_client: APIRequests = APIRequests('31u2bml5437sajwgpz6brd4j6cva')

def get_playlist_tracks(playlist: str) -> list:
    offset: int = 0
    tracks: list = []
    while True:
        print('sending fetch request ...')
        track_batch = api_client.get_playlist_tracks(playlist, offset)
        print('fetch request recieved\n---------')
        offset += 100
        for track in track_batch['items']:
            tracks.append(track['track'])
        if not track_batch["next"]:
                break
    
    return tracks

def add_tracks_to_playlist(playlist, tracks):
    for track_batch in batch(tracks, 100):
        print('sending add request ...')
        api_client.add_tracks_to_playlist(playlist, track_batch)
        print('add request recieved\n---------')

def create_playlist(name):
    print('sending create request ...')
    playlist = api_client.create_playlist(name)
    print('create request recieved\n---------')
    return playlist
    
# def create_ref_playlist():
#     with open('8194-ids.txt', 'r') as f:
#         ref_ids = eval(f.read())
    
#     ref_playlist = create_playlist('reference bit dictionary')
#     add_tracks_to_playlist(ref_playlist, ref_ids)

if __name__ == '__main__':
    pass