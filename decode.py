from main import api_request_manager, batch
import sqlite3
import os
import gzip as gz
import tkinter as tk
from tkinter import filedialog

def read(playlist: str) -> str:
    raise


def decode_file(header_playlist_id, destination):
    conn = sqlite3.connect("13bit_ids.db")
    cursor = conn.cursor()

    header_tracks = api_request_manager.get_playlist_tracks(header_playlist_id)

    header_binary = []
    for track in header_tracks:
        cursor.execute(
            "SELECT * FROM _13bit_ids WHERE track_identifier = ?",
            (
                f"{track['name']}{[artist['name'] for artist in track['artists']]}{track['album']['name']}",
            ),
        )
        binary = eval(cursor.fetchall()[0][0])
        if type(binary) is int:
            binary = [binary]
        header_binary.extend(binary)

    header_bytes = []
    for byte in batch(header_binary, 8):
        header_bytes.append(sum(bit * (2 ** (7 - idx)) for idx, bit in enumerate(byte)))

    header_string = bytes(header_bytes).decode("utf-8")
    playlist_ids = header_string.split("*")
    filename = playlist_ids.pop(0)

    total_tracks = []
    playlist_iter = 0
    for playlist in playlist_ids:
        playlist_iter += 1
        print(
            f"Fetching tracks from playlist {playlist_iter} of {len(playlist_ids)}..."
        )
        tracks = api_request_manager.get_playlist_tracks(playlist)
        total_tracks.extend(tracks)

    file_binary = []
    for track in total_tracks:
        cursor.execute(
            "SELECT * FROM _13bit_ids WHERE track_identifier = ?",
            (
                f"{track['name']}{[artist['name'] for artist in track['artists']]}{track['album']['name']}",
            ),
        )
        binary = eval(cursor.fetchall()[0][0])
        if type(binary) is int:
            binary = [binary]
        file_binary.extend(binary)

    print("Reconstructing file...")
    file_bytes = []
    for byte in batch(file_binary, 8):
        file_bytes.append(sum(bit * (2 ** (7 - idx)) for idx, bit in enumerate(byte)))

    with open(f"{filename}.gz", "wb") as f:
        f.write(bytes(file_bytes))

    with open(f"{destination}\\{filename}", "wb") as uncompressed_file:
        with gz.open(f"{filename}.gz", "rb") as compressed_file:
            uncompressed_file.write(compressed_file.read())

    os.remove(f"{filename}.gz")

    cursor.close()
    conn.close()
    return filename

def get_destination_directory():
    root = tk.Tk()
    root.withdraw()
    return filedialog.askdirectory()

if __name__ == '__main__':
    header_playlist = input('Paste header playlist URL/ID:\n\n')
    destination = get_destination_directory()
    file = decode_file(header_playlist, destination)
    print(f'File successfully decoded and saved as {file}')