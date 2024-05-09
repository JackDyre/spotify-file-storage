# Spotify File Storage


## Introduction

Experimental project that stores files as Spotify playlists.

## Usage

### Spotify API Credentials

Unfortunately with they way Spotify's API works, you must create your own API app to get your own credentials. Visit [Spotify's developer page](https://developer.spotify.com) to create your app and follow [this](https://developer.spotify.com/documentation/web-api/concepts/apps) article to get your `client_id` and `client_secret`. The program will ask you to input your API credentials once and will store them locally for future use. If at any point authentication using your API credentials fails, the `api-credentials.json` file will be removed automatically and you will recieve the API credentials prompt the next run.

### `write.py`

```
python write.py
```

Will open a file dialogue for you to select a file, then reads and converts the binary of the file to Spotify tracks. Will store the file metadata and the playlist IDs of all of the playlists that contain the contents of the file. As long as the content playlists exist, the header playlist is the only one that you need to keep track of.

### `read.py`

```
python read.py
```

Will prompt you for a header playlist ID, then open a file dialogue for you to select a destination directory, then reads and converts the Spotify track IDs to binary. Will write the file to the selected directory.

## Dependencies

Requires [spotipy](https://pypi.org/project/spotipy/) and [pyperclip](https://pypi.org/project/pyperclip/).

```
pip install spotipy
```
```
pip install pyperclip
```

