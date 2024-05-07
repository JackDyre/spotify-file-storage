import pyperclip # type: ignore
import tkinter as tk
from tkinter import filedialog
from main import api_request_manager, print_progress_bar, decimal_to_binary_padded, batch
import sqlite3
from main import ceil
import gzip as gz
import os

def get_file_path():
    root = tk.Tk()
    root.withdraw()
    return filedialog.askopenfilename()


def write_file_to_playlist(file) -> str | None:
    filename = os.path.basename(file)


    with open(file, 'rb') as uncompressed_file:
        with gz.open(f'{filename}.gz', 'wb') as compressed_file:
            compressed_file.writelines(uncompressed_file)

    with open(f'{filename}.gz', "rb") as f:  # type: ignore
        file_bytes = list(f.read())
    
    os.remove(f'{filename}.gz')

    file_binary: list = []
    for idx, byte in enumerate(file_bytes):
        print_progress_bar(idx, len(file_bytes))
        file_binary.extend(decimal_to_binary_padded(byte, 8))

    conn = sqlite3.connect("13bit_ids.db")
    cursor = conn.cursor()

    song_count = (len(file_binary) // 13) + (len(file_binary) % 13)
    playlist_count = ceil(song_count / 9_975)

    print(
        f"\n\nFile: {filename}\nRequires ~{ceil(song_count // 100)} API requests\nTime estimate: {round(ceil(song_count // 100) * .75, 0)}sec"
    )

    continue_check = input("Confirm? (Y/N) ")
    if not (continue_check == "Y" or continue_check == "y"):
        return None

    print(f"\n\nDumping {song_count} tracks into {playlist_count} playlists...\n\n")

    playlist_ids: list = []
    playlist_iter = 0
    for playlist_data in batch(file_binary, 9_975 * 13):

        track_ids: list = []

        playlist_iter += 1
        playlist_id = api_request_manager.send_request(
            api_request_manager.sp.user_playlist_create,
            user=api_request_manager.user_id,
            name=f"{filename}: Playlist {playlist_iter} of {playlist_count}",
        )["id"]
        playlist_ids.append(playlist_id)

        for track_data in batch(playlist_data, 13):
            if len(track_data) == 13:
                cursor.execute(
                    "SELECT * FROM _13bit_ids WHERE binary = ?", (str(track_data),)
                )
                track_id = cursor.fetchall()
                track_ids.append(track_id[0][1])
            else:
                for byte in track_data:
                    cursor.execute(
                        "SELECT * FROM _13bit_ids WHERE binary = ?", (str(byte),)
                    )
                    track_id = cursor.fetchall()
                    track_ids.append(track_id[0][1])

        print(f"Dumping tracks to playlist {playlist_iter} of {playlist_count}...")
        print(f"Playlist size: {len(track_ids)}\n")
        api_request_manager.add_tracks_to_playlist(playlist_id, track_ids)

    header_playlist = api_request_manager.send_request(
        request=api_request_manager.sp.user_playlist_create,
        user=api_request_manager.user_id,
        name=f"{filename}: Header Playlist",
    )["id"]
    header_string = "*".join([filename] + playlist_ids)
    header_bytes = list(header_string.encode("utf-8"))

    header_binary = []
    for idx, byte in enumerate(header_bytes):
        header_binary.extend(decimal_to_binary_padded(byte, 8))

    header_track_ids: list = []
    for header_track_data in batch(header_binary, 13):
        if len(header_track_data) == 13:
            cursor.execute(
                "SELECT * FROM _13bit_ids WHERE binary = ?",
                (str(header_track_data),),
            )
            track_id = cursor.fetchall()
            header_track_ids.append(track_id[0][1])
        else:
            for byte in header_track_data:
                cursor.execute(
                    "SELECT * FROM _13bit_ids WHERE binary = ?", (str(byte),)
                )
                track_id = cursor.fetchall()
                header_track_ids.append(track_id[0][1])

    print(f"Dumping tracks to header playlist...")
    print(f"Header size: {len(header_track_ids)}")
    api_request_manager.add_tracks_to_playlist(header_playlist, header_track_ids)

    cursor.close()
    conn.close()
    return header_playlist


if __name__ == '__main__':
    file_path = get_file_path()
    header_playlist = write_file_to_playlist(file_path)
    pyperclip.copy(header_playlist)
    print('\nHeader playlist ID copied to clipboard')