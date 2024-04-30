import sys
from math import ceil

from internal_modules.SpotifyTracksFromPlaylist import get_tracks
from internal_modules.SpotipyAPIClient import initialize_api

# sp = initialize_api(scope='playlist-read-private playlist-modify-public playlist-modify-private')
user_id = input('Input User ID: ')

ref_playlist = 'https://open.spotify.com/playlist/5qxu9APTbnKyWzhJjuMzBS?si=e99ac59e39f643dc'
ref_tracks, _ , _ = get_tracks(ref_playlist)
ref_ids = []
for track in ref_tracks:
    ref_ids.append(track['id'])

# with open("tot_ids.txt", "r") as f:
#     ref_ids = eval(f.read())


def decimal_to_binary_padded(decimal, pad):
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

with open('enc-dict.txt', 'w') as f:
    f.write(str(encode_dict))


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


def batch(iterable, batch_size):
    for i in range(0, len(iterable), batch_size):
        yield iterable[i : i + batch_size]


file = 'smol.txt'
# file = 'yo.txt'
# file = 'file-encode-playlist.py'
filename = file
with open(file, "rb") as f: # type: ignore
    file_bytes = list(f.read())

file_binary: list = []
for idx, byte in enumerate(file_bytes):
    print_progress_bar(idx, len(file_bytes))
    file_binary = file_binary + decimal_to_binary_padded(byte, 8)

print(len(file_binary))
song_count = (len(file_binary) // 13) + (len(file_binary) % 13)

playlist_count = ceil(song_count / 9_975)

print('------')
print(f'Binary len: {len(file_binary)}')
print(f'Song count: {song_count}')
print(f'Playlist count: {playlist_count}')

playlist_ids:list = []
    
playlist_track_ids = []
for playlist_data in batch(file_binary, 9_975 * 13):

    id = ''

    track_ids: list = []

    for track_data in batch(playlist_data, 13):

        if len(track_data) == 13:
            track_id = encode_dict[str(track_data)]
            track_ids.append(track_id)
        else:
            for byte in track_data:
                track_id = encode_dict[str(byte)]
                track_ids.append(track_id)

    # print(track_ids)
    # print(len(track_ids))
    playlist_track_ids.append(track_ids)

for i in playlist_track_ids:
    print(len(i))
    
