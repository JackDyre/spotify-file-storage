import sqlite3
from main import api_request_manager, batch

with sqlite3.connect("13bit_ids.db") as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM binary_to_id")
    track_ids = cursor.fetchall()
    cursor.execute("SELECT * FROM identifier_to_binary")
    track_identifiers = cursor.fetchall()

original_track_tuples: list[tuple] = []
for i in range(len(track_ids)):
    assert track_identifiers[i][1] == track_ids[i][0]
    original_track_tuples.append((track_ids[i][0], track_ids[i][1], track_identifiers[i][0]))

for chunk in batch(original_track_tuples,10_000):
    playlist_id = api_request_manager.send_request(
        request=api_request_manager.sp.user_playlist_create,
        user=api_request_manager.user_id,
        name='test'
    )['id']

    api_request_manager.add_tracks_to_playlist()


