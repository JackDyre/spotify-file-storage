from main import decode_file
import tkinter as tk
from tkinter import filedialog

def get_destination_directory():
    root = tk.Tk()
    root.withdraw()
    return filedialog.askdirectory()

if __name__ == '__main__':
    header_playlist = input('Paste header playlist URL/ID:\n\n')
    destination = get_destination_directory()
    file = decode_file(header_playlist, destination)
    print(f'File successfully decoded and saved as {file}')