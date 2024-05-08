import gzip as gz
import os
import sqlite3
import tkinter as tk
from sqlite3 import Connection, Cursor
from tkinter import filedialog
from typing import Generator, Iterable

from main import api_request_manager, batch


def read_binary_from_playlist(playlist: str, database: str) -> Generator:
    db_connection: Connection = sqlite3.connect(database)
    db_cursor: Cursor = db_connection.cursor()

    tracks: list[dict] = api_request_manager.get_playlist_tracks(playlist)
    for track in tracks:
        db_cursor.execute(
            "SELECT * FROM _13bit_ids WHERE track_identifier = ?",
            (
                f"{track['name']}{[artist['name'] for artist in track['artists']]}{track['album']['name']}",
            ),
        )
        binary: list[int] | int = eval(db_cursor.fetchall()[0][0])
        if type(binary) is int:
            binary = [binary]
        for bit in binary:  # type: ignore
            yield bit

    db_cursor.close()
    db_connection.close()


def binary_to_bytes(binary: Iterable) -> Generator:
    for byte in batch(binary, 8):
        yield sum(bit * (2 ** (7 - idx)) for idx, bit in enumerate(byte))

def confirmation_prompt(playlist_ids: list[str]) -> bool:
    total_tracks: int = 0
    for playlist in playlist_ids:
        total_tracks += api_request_manager.send_request(request=api_request_manager.sp.playlist, playlist_id=playlist)['tracks']['total']
    
    print(f'Total tracks: {total_tracks}')
    confirmation = input('Confirm (Y/N)\n')
    if confirmation.upper() == 'Y':
        return True
    return False



def read_from_playlist(header_playlist: str, destination: str, lookup_db: str = "13bit_ids.db", confirm_read: bool = False, print_progress: bool = False) -> str:

    header_string: str = bytes(
        binary_to_bytes(
            read_binary_from_playlist(header_playlist, lookup_db)
            )
    ).decode("utf-8")

    playlist_ids: list[str] = header_string.split("*")
    filename = playlist_ids.pop(0)

    file_binary: list[int] = []
    for playlist in playlist_ids:
        playlist_binary = read_binary_from_playlist(playlist, lookup_db)
        file_binary.extend(playlist_binary)
    file_bytes = binary_to_bytes(file_binary)

    with open(f"{filename}.gz", "wb") as f:
        f.write(bytes(file_bytes))

    with open(f"{destination}\\{filename}", "wb") as uncompressed_file:
        with gz.open(f"{filename}.gz", "rb") as compressed_file:
            uncompressed_file.write(compressed_file.read())

    os.remove(f"{filename}.gz")

    return f'{destination}/{filename}'


def get_destination_directory():
    root = tk.Tk()
    root.withdraw()
    return filedialog.askdirectory()


if __name__ == "__main__":
    header_playlist = input("Paste header playlist URL/ID:\n\n")
    destination = get_destination_directory()
    file = read_from_playlist(header_playlist, destination)
    print(f"File successfully decoded and saved as {file}")
