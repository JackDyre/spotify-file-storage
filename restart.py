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

class APIRequests:
    def __init__(self, user_id: str) -> None:
        self.recent_request: float = time.time()
        self.sp: spotipy.Spotify = create_client()
        self.user_id: str = user_id

    def get_playlist_tracks(self, playlist: str, offset: int, retries: int=0):
        delta_time = time.time() - self.recent_request
        if delta_time > 1:
            try:
                return self.sp.user_playlist_tracks(self.user_id, playlist, offset=offset, limit=1)
            except spotipy.exceptions.SpotifyException as e:
                if e.http_status == 429:
                    print(f'retrying: waiting {2 ** retries} seconds...')
                    time.sleep(2 ** retries)
                    retries += 1
                    return self.get_playlist_tracks(playlist, offset, retries)
                else:
                    raise e
        else:
            time.sleep(1 - delta_time)
            self.get_playlist_tracks(playlist, offset)

api_client: APIRequests = APIRequests('31u2bml5437sajwgpz6brd4j6cva')

def get_playlist_tracks(playlist: str) -> list:
    offset: int = 0
    tracks: list = []
    while True:
        print('sending request ...')
        request_batch = api_client.get_playlist_tracks(playlist, offset)
        print('request recieved')
        for track in request_batch['items']:
            tracks.append(track['track'])
        
        if not request_batch["next"]:
                break
    
    return tracks

if __name__ == '__main__':
    tracks = get_playlist_tracks('https://open.spotify.com/playlist/0aUHXLjLoyw0cfDTayFVg9?si=12023b5e99a24d94')

    print(len(tracks))

