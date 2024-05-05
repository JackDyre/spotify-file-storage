from main import api_request_manager
from main import print_progress_bar

with open('new-id-list.txt', 'r') as f:
    track_ids = eval(f.read())

with open('artist-queue.txt', 'r') as f:
    artist_queue = eval(f.read())

with open('seen-artists.txt', 'r') as f:
    seen_artists = eval(f.read())


try:
    while (artist_queue) and (len(track_ids) < ((2 ** 16) + 2)):
        artist_id = artist_queue[0]

        artist = api_request_manager.send_request(request=api_request_manager.sp.artist, artist_id=artist_id)
        print(artist['name'])

        albums: list = []
        offset = 0
        while True:
            album_batch = api_request_manager.send_request(request=api_request_manager.sp.artist_albums, artist_id=artist_id, limit=50, offset=offset)
            albums.extend(album_batch['items'])
            offset += 50
            if not album_batch['next']:
                break

        for album in albums:
            tracks = api_request_manager.send_request(request=api_request_manager.sp.album_tracks, album_id=album['id'])
            print_progress_bar(albums.index(album), len(albums))

            for track in tracks['items']:
                if track['id'] not in track_ids:
                    track_ids.append(track['id'])
                for artist in track['artists']:
                    if not ((artist['id'] in artist_queue) or (artist['id'] in seen_artists)):
                        artist_queue.append(artist['id'])
        print('\n\n')
        print(f'Track List Length: {len(track_ids)}/{2**16 + 2} | {100 * len(track_ids)/(2**16 + 2)}')
        print(f'Artist Queue Length: {len(artist_queue)}')
        print('\n\n\n')

        seen_artists.append(artist_queue.pop(0))

        with open('new-id-list.txt', 'w') as f:
            f.write(str(track_ids)) 
        with open('artist-queue.txt', 'w') as f:
            f.write(str(artist_queue))    
        with open('seen-artists.txt', 'w') as f:
            f.write(str(seen_artists)) 

finally:
    with open('new-id-list.txt', 'w') as f:
        f.write(str(track_ids)) 
    with open('artist-queue.txt', 'w') as f:
        f.write(str(artist_queue))    
    with open('seen-artists.txt', 'w') as f:
        f.write(str(seen_artists)) 
    
