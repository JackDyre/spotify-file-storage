"""Uses spotipy to create a Spotify API client."""
import tkinter as tk
import sys

import spotipy  # type: ignore
from spotipy.oauth2 import SpotifyOAuth  # type: ignore

from internal_modules.PyBinaryFile import init_serialized_file


def get_api_vars() -> tuple[str, str]:

    api_vars_file = init_serialized_file(
        "client_id_client_secret", file_extension=".APIcredentials"
    )
    if "[ERROR]" in api_vars_file.read:
        client_id, client_secret = api_vars_prompt()
        api_vars_file.write({"client_id": client_id, "client_secret": client_secret})
    else:
        api_vars = api_vars_file.read
        client_id, client_secret = api_vars["client_id"], api_vars["client_secret"]

    return (client_id, client_secret)


def api_vars_prompt() -> tuple[str, str]:

    def get_api_creds():
        nonlocal client_id, client_secret
        client_id = id.get()
        client_secret = secret.get()
        root.destroy()

    client_id = ''
    client_secret = ''

    width: int = 250
    height: int = 200

    root = tk.Tk()
    root.title('Input Spotify API credentials')

    left = (root.winfo_screenwidth() - width)//2
    top = (root.winfo_screenheight() - height)//2
    root.geometry(f'{width}x{height}+{left}+{top}')

    frame = tk.Frame(root)
    frame.pack(expand=True)

    tk.Label(frame, text='Input client ID:').pack(pady=5)

    id = tk.Entry(frame, width=30)
    id.pack(pady=5)

    tk.Label(frame, text='Input client secret:').pack(pady=5)

    secret = tk.Entry(frame, width=30)
    secret.pack(pady=5)

    tk.Button(frame, text='Enter', command=get_api_creds).pack(pady=5)

    tk.mainloop()


    if len(client_id) != 32 or len(client_id) != 32:
        print("Invalid API credentials: Please try again")
        sys.exit()

    return (client_id, client_secret)


def initialize_api(scope=None):
    """
    Creates a Spotify API client using spotipy.

    Scopes:
        - playlist-read-private: Allows read access to user's private playlists.
        - playlist-read-collaborative: Allows read access to user's collaborative playlists.
        - playlist-modify-public: Allows modifying user's public playlists. This includes creating and adding tracks to playlists.
        - playlist-modify-private: Allows modifying user's private playlists. This includes creating and adding tracks to playlists.
        - user-library-read: Allows read access to a user's "Your Music" library.
        - user-library-modify: Allows modifying a user's "Your Music" library. This includes adding, removing, and arranging tracks in the library.
        - user-read-private: Allows reading access to user's private information such as display name and email address.
        - user-read-email: Allows reading access to user's email address.
        - user-read-playback-state: Allows reading access to a user's playback state (e.g., current track, position, etc.).
        - user-modify-playback-state: Allows modifying a user's playback state (e.g., starting playback, pausing, skipping to the next track, etc.).
        - user-read-currently-playing: Allows reading access to the currently playing track for a user.
        - user-read-recently-played: Allows reading access to a user's recently played tracks.
        - user-follow-read: Allows reading access to the list of users the current user follows.
        - user-follow-modify: Allows modifying the list of users the current user follows.
        - user-top-read: Allows reading access to a user's top artists and tracks.
        - user-read-playback-position: Allows reading access to a user's playback position in a content item.
    """

    client_id, client_secret = get_api_vars()

    try:
        sp = spotipy.Spotify(
            auth_manager=SpotifyOAuth(
                client_id=client_id,
                client_secret=client_secret,
                scope=scope,
                redirect_uri="http://localhost:8888/callback",
            )
        )
    except Exception as e:
        print(f"An API error was encountered. Please try again\n{e}")
    return sp
