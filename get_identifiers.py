from main import api_request_manager, print_progress_bar

import json

with open('13bit_ids.json',  'r') as f:
    x = json.load(f)

g = api_request_manager.get_playlist_tracks(playlist='6jNNX4nv5SpoggrwBNx017')

stri=[]
for q in g:
    stri.append(f"{q['name']}{[artist['name'] for artist in q['artists']]}")

with open('13bit_indentifiers.json',  'w') as f:
    json.dump(stri, f)