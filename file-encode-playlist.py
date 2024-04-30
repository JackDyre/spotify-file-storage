from internal_modules.SpotifyTracksFromPlaylist import get_tracks
from math import ceil
from internal_modules.SpotipyAPIClient import initialize_api


sp = initialize_api(scope='playlist-read-private playlist-modify-public playlist-modify-private')
user_id = input('Input User ID: ')

ref_playlist = 'https://open.spotify.com/playlist/5qxu9APTbnKyWzhJjuMzBS?si=15e677b542c846f5'
ref_tracks, q , w = get_tracks(ref_playlist)
ref_ids = []
for track in ref_tracks:
    ref_ids.append(track['id'])


def decimal_to_binary_padded(decimal,pad):
    binary = ""
    while decimal > 0:
        remainder = decimal % 2
        binary = str(remainder) + binary
        decimal = decimal // 2
    binary = binary.zfill(pad)
    return [int(bit) for bit in binary]


encode_dict = {}
for idx, id in enumerate(ref_ids[:8192]):
    encode_dict[str(decimal_to_binary_padded(idx, 13))] = id
for idx, id in enumerate(ref_ids[-2:]):
    encode_dict[str(idx)] = id


import sys
import time

def print_progress_bar(iteration, total, prefix='', suffix='', length=50, fill='█'):
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
    bar = fill * filled_length + '-' * (length - filled_length)
    sys.stdout.write('\r%s |%s| %s%% %s' % (prefix, bar, percent, suffix)),
    sys.stdout.flush()
    if iteration == total:
        sys.stdout.write('\n')
        sys.stdout.flush()


def batch(iterable, batch_size):
    for i in range(0, len(iterable), batch_size):
        yield iterable[i:i + batch_size]

file = 'smol.txt.txt'
# file = 'yo.txt'
# file = 'file-encode-playlist.py'
filename = file
with open(file, 'rb') as f:
    file_bytes = list(f.read())

file_binary: list = []
for idx, byte in enumerate(file_bytes):
    print_progress_bar(idx, len(file_bytes))
    file_binary = file_binary + decimal_to_binary_padded(byte, 8)

print(len(file_binary))
song_count = (len(file_binary) // 13) + (len(file_binary) % 13)

playlist_count = ceil(song_count/9_975)

print(playlist_count)


playlist_ids: list = []
data_batched_for_playlists = batch(file_binary, 9_975)
for i in range(playlist_count):
    playlist = sp.user_playlist_create(user=user_id, name=f'{filename} Playlist {i + 1} of {playlist_count}')
    playlist_ids.append(playlist['id'])

    playlist_data_batch = list(data_batched_for_playlists)[i]
    track_ids = []
    for idx, track_data_batch in enumerate(batch(playlist_data_batch, 13)):
        if len(track_data_batch) == 13:
            track_ids.append(encode_dict[str(track_data_batch)])          
        else: 
            for byte in track_data_batch:
                track_ids.append(encode_dict[str(byte)])
        
    for track_batch in batch(track_ids, 100):
        sp.user_playlist_add_tracks(user=user_id, playlist_id=playlist['id'], tracks=track_batch)

