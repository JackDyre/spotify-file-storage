from main import api_request_manager, print_progress_bar

import json

with open('13bit_ids.json',  'r') as f:
    x = json.load(f)

g = api_request_manager.get_playlist_tracks(playlist='6jNNX4nv5SpoggrwBNx017')

for q in range(len(x)):
    if not x[q] == g[q]['id']:
        print(f'{g[q]['artists'][0]['name']} - {g[q]['name']}')
        print(f'Original: {x[q]}')
        print(f'Now Returning: {g[q]['id']}\n')

        x[q] = g[q]['id']

with open('13bit_ids.json',  'w') as f:
    json.dump(x, f)