from internal_modules.SpotipyAPIClient import initialize_api
from internal_modules.SpotifyTracksFromPlaylist import get_tracks

sp = initialize_api(scope='playlist-read-private playlist-modify-public playlist-modify-private')


user_id = '31u2bml5437sajwgpz6brd4j6cva'
x = sp.user_playlist_create(user=user_id, name='ref test')

def batch(iterable, batch_size):
    for i in range(0, len(iterable), batch_size):
        yield iterable[i:i + batch_size]




with open('tot_ids.txt', 'r') as f:
    ids = eval(f.read())

ids_s = ids[:100]

for batch_ids in batch(ids, 100):
    # Call the API function with the current batch of IDs
    sp.user_playlist_add_tracks(user=user_id, playlist_id=x['id'], tracks=batch_ids)

# with open('test.txt', 'w') as f:
#     f.write(str(x))

# yelr_tracks, _ , _ = get_tracks(url='https://open.spotify.com/playlist/2YiN80y1p4w69tb4sx8RcX?si=5c2ea201fe2b47a4')

# yelr_ids = []
# for track in yelr_tracks:
#     yelr_ids.append(track['id'])

# with open('yelr_ids.txt', 'w') as f:
#     f.write(str(yelr_ids))

# ids_8192 = []
# with open('yelr_ids.txt', 'r') as f:
#     yelr_ids = f.read()
#     yelr_ids = eval(yelr_ids)
#     for id in yelr_ids:
#         ids_8192.append(id)
# print(len(ids_8192))

# noc_tracks, _ , _ = get_tracks(url='https://open.spotify.com/playlist/0kSPkIGZGUHVPBQo3TySfK?si=3e5c6693830a4a45')

# noc_ids = []
# for track in noc_tracks:
#     noc_ids.append(track['id'])

# with open('noc_ids.txt', 'w') as f:
#     f.write(str(noc_ids))


# with open('noc_ids.txt', 'r') as f:
#     noc_ids = f.read()
#     noc_ids = eval(noc_ids)
# print(len(noc_ids))

# for id in noc_ids:
#     if id not in ids_8192:
#         ids_8192.append(id)
    
#     if len(ids_8192) == 8192:
#         break

# print(len(ids_8192))

# with open('tot_ids.txt', 'w') as f:
#     f.write(str(ids_8192))

